"""
====================================================
Safe5G Threat Engine
====================================================
"""

import json
from pathlib import Path

from rules.zones import ZoneManager


class RuleEngine:

    def __init__(self):

        weight_file = Path(__file__).parent / "weights.json"

        with open(weight_file, "r") as f:

            self.weights = json.load(f)

        self.zone_manager = ZoneManager()

    # ------------------------------------------------

    def evaluate(self, person):

        person.clear_rules()

        score = 0

        # ---------------------------------------------
        # Loitering
        # ---------------------------------------------

        if person.time_seen > 15:

            score += self.weights["loitering"]

            person.add_rule("Loitering")

        # ---------------------------------------------
        # Running
        # ---------------------------------------------

        if person.velocity > 40:

            score += self.weights["running"]

            person.add_rule("Running")

        # ---------------------------------------------
        # Restricted Zone
        # ---------------------------------------------

        zone = self.zone_manager.get_active_zone(

            person.center

        )

        if zone is not None:

            score += self.weights["restricted_zone"]

            person.add_rule(zone.name)

        # ---------------------------------------------
        # Crowd
        # (implemented later)
        # ---------------------------------------------

        # ---------------------------------------------
        # Following
        # (implemented later)
        # ---------------------------------------------

        if score > 100:

            score = 100

        person.set_threat(score)

        return person