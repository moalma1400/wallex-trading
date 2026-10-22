# Competition-specific market eligibility configuration.

from . import DataSource, Eligibility, EligibilityResult, MarketMeta
from .provider import MarketEligibilityGate


def configure_elcamp_gate() -> MarketEligibilityGate:
    """Create a MarketEligibilityGate pre-configured for Elcamp competition.

    For now, no markets are explicitly allowed. This prevents accidental
    trading on unverified markets.
    """
    gate = MarketEligibilityGate()

    # Explicitly prohibited risky markets
    gate.prohibit("PUMPTMN", reason="isRisky flagged pump-fun token")
    gate.prohibit("MOGTMN", reason="isRisky flagged memecoin")
    gate.prohibit("MOGUSDT", reason="isRisky flagged memecoin")
    gate.prohibit("SANDTMN", reason="isRisky flagged")
    gate.prohibit("FLOWTMN", reason="isRisky flagged")
    gate.prohibit("DEXEUSDT", reason="isRisky flagged")
    gate.prohibit("PNUTUSDT", reason="isRisky flagged")
    gate.prohibit("XLMTMN", reason="isRisky flagged")

    return gate
