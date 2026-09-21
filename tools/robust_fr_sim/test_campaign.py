#!/usr/bin/env python3
"""Offline integration regressions; never launches a robot executable."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from campaign import BIN, MODEL, variations, perturb, run


class CampaignTests(unittest.TestCase):
    def test_reproducible_paired_variations(self):
        a=variations(20260921,100)
        self.assertEqual(a,variations(20260921,100))
        self.assertEqual(sum(p["sphere-only"]==0 for p in a),20)
        for nominal in [{"kp":60,"kd":.7},{"kp":100,"kd":2.5}]:
            samples=[perturb(nominal,p) for p in a]
            self.assertTrue(all(60<=p["kp"]<=100 and .7<=p["kd"]<=2.5 for p in samples))
            self.assertTrue(all(abs(p["kp"]-nominal["kp"])<=.1*nominal["kp"]+.0001 for p in samples))

    def test_geometry(self):
        subprocess.run([str(BIN),"--self-test"],check=True)

    def test_unload_blocks_requested_lift(self):
        with tempfile.TemporaryDirectory(prefix="lite3-offline-test-") as tmp:
            record=run(("denied_lift",{"sphere-only":1,"duration":2,"lift":.005},Path(tmp)))
            self.assertTrue(record["stand_pass"])
            self.assertTrue(record["safe"])
            self.assertFalse(record["unload_pass"])
            self.assertFalse(record["lift_pass"])
            self.assertEqual(record["max_target_delta_rad"],0)
            self.assertAlmostEqual(record["weight_stand_n"],11.9376*9.81,delta=.1)

    def test_envelope_rejects_large_shift(self):
        with tempfile.TemporaryDirectory(prefix="lite3-offline-test-") as tmp:
            record=run(("too_large",{"sphere-only":1,"duration":2,"x":-.03,"y":.03},Path(tmp)))
            self.assertFalse(record["plan_pass"])
            self.assertFalse(record["unload_pass"])
            self.assertEqual(record["first_failure"],"command_envelope")

    def test_unapproved_gains_rejected(self):
        with tempfile.TemporaryDirectory(prefix="lite3-offline-test-") as tmp:
            result=subprocess.run([str(BIN),"--model",str(MODEL),"--out",tmp+"/invalid","--kp","180"],capture_output=True)
            self.assertNotEqual(result.returncode,0)

    def test_payload_offset_changes_load_distribution(self):
        with tempfile.TemporaryDirectory(prefix="lite3-offline-test-") as tmp:
            common={"sphere-only":1,"duration":2,"payload":1.5,"kp":60,"kd":.7}
            forward=run(("forward",{**common,"com-x":.08},Path(tmp)))
            rear=run(("rear",{**common,"com-x":-.08},Path(tmp)))
            self.assertGreater(forward["fr_fraction_stand"]-rear["fr_fraction_stand"],.005)


if __name__=="__main__":unittest.main()
