import unittest

from opendbc.car import gen_empty_fingerprint, structs
from opendbc.car.chrysler.carcontroller import CarController
from opendbc.car.chrysler.carstate import CarState
from opendbc.car.chrysler.interface import CarInterface
from opendbc.car.chrysler.values import CAR, DBC, ChryslerFlags


def params(candidate=CAR.JEEP_GRAND_CHEROKEE_2019, marker=True, bus=0, length=4):
  fingerprint = gen_empty_fingerprint()
  if marker:
    fingerprint[bus][0x4FF] = length
  return CarInterface.get_params(candidate, fingerprint, [], False, True, False)


class TestWpmod(unittest.TestCase):
  def setUp(self):
    self.cp = params()
    self.cs = CarState(self.cp)
    self.cs.out = structs.CarState(vEgo=1., steeringTorqueEps=0.)
    self.cc = structs.CarControl(enabled=True, latActive=True)
    self.cc.actuators.torque = 1.
    self.controller = CarController(DBC[self.cp.carFingerprint], self.cp)
    self.controller.frame = 202

  def command(self, controller=None):
    controller = controller or self.controller
    if controller.frame % 2:
      controller.update(self.cc.as_reader(), self.cs, controller.frame * 10_000_000)
    _, messages = controller.update(self.cc.as_reader(), self.cs, controller.frame * 10_000_000)
    _, data, bus = next(m for m in messages if m[0] == 658)
    self.assertEqual(bus, 0)
    self.assertEqual(len(data), 6)
    return bool(data[0] & 0x10), (((data[0] & 7) << 8) | data[1]) - 1024

  def test_detected_wk2_changes_only_flag_and_speed(self):
    stock = params(marker=False)
    self.assertEqual(stock.minSteerSpeed, 17.5)
    self.assertEqual(self.cp.minSteerSpeed, 0.)
    self.assertTrue(self.cp.flags & ChryslerFlags.WP_MOD)
    expected = stock.to_dict()
    expected['minSteerSpeed'] = 0.
    expected['flags'] |= ChryslerFlags.WP_MOD.value
    self.assertEqual(self.cp.to_dict(), expected)
    self.assertFalse(self.cp.steerAtStandstill)
    self.assertFalse(self.cp.openpilotLongitudinalControl)

  def test_wrong_bus_or_length_does_not_enable(self):
    for kwargs in ({'marker': False}, {'bus': 1}, {'bus': 2}, {'length': 0}, {'length': 8}):
      with self.subTest(kwargs=kwargs):
        cp = params(**kwargs)
        self.assertEqual(cp.minSteerSpeed, 17.5)
        self.assertFalse(cp.flags & ChryslerFlags.WP_MOD)

  def test_other_chrysler_platforms_unchanged(self):
    for candidate in CAR:
      if candidate == CAR.JEEP_GRAND_CHEROKEE_2019:
        continue
      with self.subTest(candidate=candidate):
        self.assertEqual(params(candidate, True).to_dict(), params(candidate, False).to_dict())

  def test_active_steering_at_low_speed(self):
    for speed in (0.31, 1., 5., 10., 17.4, 30.):
      with self.subTest(speed=speed):
        self.cs.out.vEgo = speed
        active, torque = self.command()
        self.assertTrue(active)
        self.assertLessEqual(abs(torque), 80)

  def test_ready_or_lateral_off_clears_bit_and_torque(self):
    self.command()
    self.command()
    self.cc.latActive = False
    for speed in (1., 20.):
      self.cs.out.vEgo = speed
      self.assertEqual(self.command(), (False, 0))

  def test_reengagement_waits_two_seconds(self):
    self.assertTrue(self.command()[0])
    self.cc.latActive = False
    self.assertEqual(self.command(), (False, 0))
    falling = self.controller.last_lkas_falling_edge
    self.cc.latActive = True
    self.controller.frame = falling + 200
    self.assertEqual(self.command(), (False, 0))
    self.assertTrue(self.command()[0])

  def test_torque_and_rate_limits_remain(self):
    previous = 0
    for _ in range(120):
      self.cs.out.steeringTorqueEps = previous
      active, torque = self.command()
      self.assertTrue(active)
      self.assertLessEqual(abs(torque), 261)
      self.assertLessEqual(torque - previous, 3)
      previous = torque
    self.assertEqual(previous, 261)
    self.cc.latActive = False
    self.assertEqual(self.command(), (False, 0))

  def test_without_wpmod_keeps_original_speed_hysteresis(self):
    stock_cp = params(marker=False)
    stock_controller = CarController(DBC[stock_cp.carFingerprint], stock_cp)
    stock_controller.frame = 202
    self.cs.out.vEgo = 1.
    self.assertEqual(self.command(stock_controller), (False, 0))
    self.cs.out.vEgo = 18.
    self.assertTrue(self.command(stock_controller)[0])
    self.cs.out.vEgo = 15.
    self.assertTrue(self.command(stock_controller)[0])
    self.cs.out.vEgo = 14.
    self.assertEqual(self.command(stock_controller), (False, 0))


if __name__ == '__main__':
  unittest.main(verbosity=2)
