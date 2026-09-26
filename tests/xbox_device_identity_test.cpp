#include "xbox_gamepad_interface.hpp"

#include <cassert>
#include <iostream>

int main() {
    assert(XboxGamepadInterface::IsKnownBluetoothDeviceName(
        "Xbox Wireless Controller"));
    assert(!XboxGamepadInterface::IsKnownBluetoothDeviceName(
        "Microsoft X-Box One pad"));
    assert(!XboxGamepadInterface::IsKnownBluetoothDeviceName("Generic Joystick"));
    std::cout<<"xbox_device_identity_test PASS\n";
}
