"""
Glicko-2 Rating System Implementation

Based on: http://www.glicko.net/glicko/glicko2.pdf
Author: Professor Mark Glickman

Glicko-2 is an improvement over the Elo rating system that:
1. Adds rating deviation (RD) to quantify uncertainty
2. Adds volatility (σ) to measure rating consistency
3. Handles infrequent play periods better
4. Produces more accurate ratings for sparse data

This implementation is framework-agnostic (no UI dependencies)
and fully testable with pure Python.
"""

import math
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class RatingUpdate:
    """Result of a rating update"""
    rating: float
    rating_deviation: float
    volatility: float


@dataclass
class Opponent:
    """Opponent information for a comparison"""
    rating: float
    rating_deviation: float
    outcome: float  # 1.0 = win, 0.5 = draw, 0.0 = loss


class Glicko2Calculator:
    """
    Glicko-2 rating calculator
    
    Supports:
    - Wins, losses, and draws
    - Partial outcomes (e.g., 0.75 for "slight win")
    - Multiple games in one rating period
    - Inactivity decay (RD increases over time)
    
    Example:
        calc = Glicko2Calculator(tau=0.5)
        
        # Song A (1500, RD=350) beats Song B (1600, RD=200)
        new_rating = calc.update_rating(
            rating=1500,
            rd=350,
            volatility=0.06,
            opponents=[
                Opponent(rating=1600, rating_deviation=200, outcome=1.0)
            ]
        )
        
        print(f"New rating: {new_rating.rating:.0f}")
        print(f"New RD: {new_rating.rating_deviation:.0f}")
        print(f"Confidence: {calc.get_confidence(new_rating.rating_deviation)}")
    """
    
    # Constants
    SCALE = 173.7178  # Conversion between Glicko and Glicko-2 scale
    EPSILON = 0.000001  # Convergence tolerance for volatility calculation
    
    def __init__(self, tau: float = 0.5):
        """
        Initialize Glicko-2 calculator
        
        Args:
            tau: System constant that constrains volatility changes (0.3 to 1.2)
                 - Lower values (0.3-0.5): More stable, slower adaptation
                 - Higher values (0.8-1.2): Faster adaptation, more volatile
                 - Default 0.5 is recommended for most use cases
        """
        if not 0.2 <= tau <= 1.5:
            raise ValueError(f"tau must be between 0.2 and 1.5, got {tau}")
        
        self.tau = tau
    
    def _scale_to_glicko2(self, rating: float, rd: float) -> Tuple[float, float]:
        """
        Convert from Glicko scale to Glicko-2 scale
        
        Glicko-2 uses a different scale for internal calculations
        to keep the math well-conditioned
        
        Args:
            rating: Rating on Glicko scale (~1500)
            rd: Rating deviation on Glicko scale (~350)
        
        Returns:
            (mu, phi) on Glicko-2 scale
        """
        mu = (rating - 1500) / self.SCALE
        phi = rd / self.SCALE
        return mu, phi
    
    def _scale_to_glicko(self, mu: float, phi: float) -> Tuple[float, float]:
        """
        Convert from Glicko-2 scale back to Glicko scale
        
        Args:
            mu: Rating on Glicko-2 scale
            phi: Rating deviation on Glicko-2 scale
        
        Returns:
            (rating, rd) on Glicko scale
        """
        rating = mu * self.SCALE + 1500
        rd = phi * self.SCALE
        return rating, rd
    
    def _g(self, phi: float) -> float:
        """
        g(φ) function - reduces impact of opponent with high RD
        
        Intuition: An opponent with high uncertainty (high RD) provides
        less information, so their rating matters less in the calculation
        
        Args:
            phi: Opponent's rating deviation (Glicko-2 scale)
        
        Returns:
            g(phi) value between 0 and 1
        """
        return 1 / math.sqrt(1 + 3 * phi**2 / math.pi**2)
    
    def _E(self, mu: float, mu_j: float, phi_j: float) -> float:
        """
        E(μ, μⱼ, φⱼ) - Expected outcome
        
        Calculates the probability that player with rating mu
        will beat player with rating mu_j and RD phi_j
        
        Args:
            mu: Player's rating (Glicko-2 scale)
            mu_j: Opponent's rating (Glicko-2 scale)
            phi_j: Opponent's RD (Glicko-2 scale)
        
        Returns:
            Expected score (0 to 1)
        """
        return 1 / (1 + math.exp(-self._g(phi_j) * (mu - mu_j)))
    
    def _v(self, mu: float, opponents: List[Tuple[float, float]]) -> float:
        """
        Calculate variance (inverse of information)
        
        Args:
            mu: Player's rating (Glicko-2 scale)
            opponents: List of (mu_j, phi_j) for each opponent
        
        Returns:
            Variance estimate
        """
        v_inv = 0
        for mu_j, phi_j in opponents:
            E = self._E(mu, mu_j, phi_j)
            g = self._g(phi_j)
            v_inv += g**2 * E * (1 - E)
        
        return 1 / v_inv if v_inv > 0 else float('inf')
    
    def _delta(self, mu: float, v: float, outcomes: List[Tuple[Tuple[float, float], float]]) -> float:
        """
        Calculate delta (improvement in rating based on results)
        
        Args:
            mu: Player's rating (Glicko-2 scale)
            v: Variance
            outcomes: List of ((mu_j, phi_j), outcome) for each game
        
        Returns:
            Delta value
        """
        delta_sum = 0
        for (mu_j, phi_j), s in outcomes:
            g = self._g(phi_j)
            E = self._E(mu, mu_j, phi_j)
            delta_sum += g * (s - E)
        
        return v * delta_sum
    
    def _new_volatility(self, phi: float, sigma: float, v: float, delta: float) -> float:
        """
        Calculate new volatility using Illinois algorithm
        
        This is the most complex part of Glicko-2!
        Uses iterative root-finding to solve for new volatility
        
        Args:
            phi: Current RD (Glicko-2 scale)
            sigma: Current volatility
            v: Variance
            delta: Rating improvement
        
        Returns:
            New volatility
        """
        a = math.log(sigma**2)
        
        def f(x):
            """Function we're finding the root of"""
            ex = math.exp(x)
            num1 = ex * (delta**2 - phi**2 - v - ex)
            denom1 = 2 * (phi**2 + v + ex)**2
            num2 = x - a
            denom2 = self.tau**2
            return num1 / denom1 - num2 / denom2
        
        # Initialize bounds for Illinois algorithm
        A = a
        if delta**2 > phi**2 + v:
            B = math.log(delta**2 - phi**2 - v)
        else:
            k = 1
            while f(a - k * self.tau) < 0:
                k += 1
            B = a - k * self.tau
        
        # Iterate using Illinois algorithm
        fA = f(A)
        fB = f(B)
        
        while abs(B - A) > self.EPSILON:
            C = A + (A - B) * fA / (fB - fA)
            fC = f(C)
            
            if fC * fB < 0:
                A = B
                fA = fB
            else:
                fA = fA / 2
            
            B = C
            fB = fC
        
        return math.exp(A / 2)
    
    def update_rating(
        self,
        rating: float,
        rd: float,
        volatility: float,
        opponents: List[Opponent],
        days_since_last: int = 0
    ) -> RatingUpdate:
        """
        Update rating after one or more games
        
        Args:
            rating: Current rating (Glicko scale, ~1500)
            rd: Current rating deviation (Glicko scale, ~350 for new)
            volatility: Current volatility (~0.06)
            opponents: List of Opponent objects with rating, rd, and outcome
                      outcome: 1.0 = win, 0.5 = draw, 0.0 = loss
                      Can also use partial values like 0.75 for "slight win"
            days_since_last: Days since last game (for RD increase)
        
        Returns:
            RatingUpdate with new rating, rd, and volatility
        
        Example:
            # Won against higher-rated opponent
            result = calc.update_rating(
                rating=1500,
                rd=350,
                volatility=0.06,
                opponents=[
                    Opponent(rating=1700, rating_deviation=100, outcome=1.0)
                ],
                days_since_last=0
            )
        """
        # Handle inactivity - RD increases over time
        if days_since_last > 0:
            rd_increase = days_since_last * 0.5  # Configurable
            rd = min(350, math.sqrt(rd**2 + rd_increase))
        
        # If no games played, only RD changes
        if not opponents:
            return RatingUpdate(rating=rating, rating_deviation=rd, volatility=volatility)
        
        # Step 1: Convert to Glicko-2 scale
        mu, phi = self._scale_to_glicko2(rating, rd)
        
        # Step 2: Convert opponents to Glicko-2 scale
        opponents_g2 = []
        outcomes = []
        for opp in opponents:
            opp_mu, opp_phi = self._scale_to_glicko2(opp.rating, opp.rating_deviation)
            opponents_g2.append((opp_mu, opp_phi))
            outcomes.append(((opp_mu, opp_phi), opp.outcome))
        
        # Step 3: Calculate variance
        v = self._v(mu, opponents_g2)
        
        # Step 4: Calculate delta (rating improvement)
        delta = self._delta(mu, v, outcomes)
        
        # Step 5: Calculate new volatility
        new_sigma = self._new_volatility(phi, volatility, v, delta)
        
        # Step 6: Update rating deviation (pre-rating period)
        phi_star = math.sqrt(phi**2 + new_sigma**2)
        
        # Step 7: Update rating and RD
        new_phi = 1 / math.sqrt(1/phi_star**2 + 1/v)
        
        improvement = 0
        for (mu_j, phi_j), s in outcomes:
            improvement += self._g(phi_j) * (s - self._E(mu, mu_j, phi_j))
        
        new_mu = mu + new_phi**2 * improvement
        
        # Step 8: Convert back to Glicko scale
        new_rating, new_rd = self._scale_to_glicko(new_mu, new_phi)
        
        return RatingUpdate(
            rating=new_rating,
            rating_deviation=new_rd,
            volatility=new_sigma
        )
    
    def win_probability(
        self,
        rating_a: float,
        rd_a: float,
        rating_b: float,
        rd_b: float
    ) -> float:
        """
        Calculate probability that A beats B
        
        Accounts for rating deviation (uncertainty)
        More uncertain ratings → closer to 50/50
        
        Args:
            rating_a: A's rating
            rd_a: A's rating deviation
            rating_b: B's rating
            rd_b: B's rating deviation
        
        Returns:
            Probability A wins (0.0 to 1.0)
        
        Example:
            prob = calc.win_probability(
                rating_a=1700, rd_a=50,   # Confident high rating
                rating_b=1500, rd_b=350   # Uncertain average rating
            )
            # Returns ~0.75 (75% chance A wins)
        """
        mu_a, phi_a = self._scale_to_glicko2(rating_a, rd_a)
        mu_b, phi_b = self._scale_to_glicko2(rating_b, rd_b)
        
        return self._E(mu_a, mu_b, phi_b)
    
    def confidence_interval(
        self,
        rating: float,
        rd: float,
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval for rating
        
        Args:
            rating: Current rating
            rd: Rating deviation
            confidence: Confidence level (0.90, 0.95, or 0.99)
        
        Returns:
            (lower_bound, upper_bound)
        
        Example:
            lower, upper = calc.confidence_interval(1687, 150, 0.95)
            # Returns (1393, 1981)
            # We're 95% confident the true rating is between 1393-1981
        """
        # Z-scores for confidence levels
        z_scores = {
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576
        }
        
        z = z_scores.get(confidence, 1.96)
        margin = z * rd
        
        return (rating - margin, rating + margin)
    
    def get_confidence(self, rd: float) -> str:
        """
        Get human-readable confidence level
        
        Args:
            rd: Rating deviation
        
        Returns:
            Confidence description
        
        Example:
            calc.get_confidence(50)   # "Very Confident"
            calc.get_confidence(200)  # "Moderately Confident"
            calc.get_confidence(350)  # "Uncertain"
        """
        if rd < 100:
            return "Very Confident"
        elif rd < 200:
            return "Confident"
        elif rd < 300:
            return "Moderately Confident"
        else:
            return "Uncertain"
    
    def expected_rating_change(
        self,
        rating: float,
        rd: float,
        opponent_rating: float,
        opponent_rd: float,
        outcome: float
    ) -> float:
        """
        Estimate how much rating will change given an outcome
        
        Useful for showing users impact before they make a choice
        
        Args:
            rating: Current rating
            rd: Current RD
            opponent_rating: Opponent's rating
            opponent_rd: Opponent's RD
            outcome: Expected outcome (1.0 = win, 0.5 = draw, 0.0 = loss)
        
        Returns:
            Estimated rating change (can be negative)
        """
        result = self.update_rating(
            rating=rating,
            rd=rd,
            volatility=0.06,  # Assume default
            opponents=[Opponent(opponent_rating, opponent_rd, outcome)]
        )
        
        return result.rating - rating


# Example usage
if __name__ == '__main__':
    calc = Glicko2Calculator(tau=0.5)
    
    print("=" * 60)
    print("Glicko-2 Calculator Example")
    print("=" * 60)
    
    # Scenario: New song (1500 ± 350) beats established favorite (1700 ± 50)
    print("\nScenario: Upset victory")
    print("New song (1500 ± 350) beats Favorite (1700 ± 50)")
    
    result = calc.update_rating(
        rating=1500,
        rd=350,
        volatility=0.06,
        opponents=[
            Opponent(rating=1700, rating_deviation=50, outcome=1.0)
        ]
    )
    
    print(f"\nNew song rating: 1500 → {result.rating:.0f} (+{result.rating - 1500:.0f})")
    print(f"RD: 350 → {result.rating_deviation:.0f}")
    print(f"Volatility: 0.06 → {result.volatility:.4f}")
    
    ci_lower, ci_upper = calc.confidence_interval(result.rating, result.rating_deviation)
    print(f"95% Confidence Interval: [{ci_lower:.0f}, {ci_upper:.0f}]")
    print(f"Confidence: {calc.get_confidence(result.rating_deviation)}")
    
    # Scenario: Draw between equal opponents
    print("\n" + "=" * 60)
    print("\nScenario: Draw between equals")
    print("Song A (1500 ± 200) draws with Song B (1500 ± 200)")
    
    result_draw = calc.update_rating(
        rating=1500,
        rd=200,
        volatility=0.06,
        opponents=[
            Opponent(rating=1500, rating_deviation=200, outcome=0.5)
        ]
    )
    
    print(f"\nSong A rating: 1500 → {result_draw.rating:.0f} ({result_draw.rating - 1500:+.0f})")
    print(f"RD: 200 → {result_draw.rating_deviation:.0f}")
    print(f"Volatility: 0.06 → {result_draw.volatility:.4f}")
    
    print("\n" + "=" * 60)
