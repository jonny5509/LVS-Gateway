#include "bluetooth_service.h"

void bluetooth_service_init() {
  // Advertise a conventional LVS-prefixed name for compatibility testing. A name change alone does not guarantee Lovense Connect recognition.
  NimBLEDevice::init("LVS-ESP32");

  // Create the GATT server used by the Lovense-compatible phone interface.
  NimBLEDevice::createServer();

  NimBLEAdvertising *pAdvertising = NimBLEDevice::getAdvertising();
  pAdvertising->setScanResponse(true);

  // The same advertisement carries MuSE/LoveSpouse manufacturer commands.
  // Their documented protocol requires an advertising interval of at least
  // 250 ms; BLE interval units are 0.625 ms, so 0x0190 = 250 ms.
  pAdvertising->setMinInterval(0x0190);
  pAdvertising->setMaxInterval(0x0190);

  // Preferred connection interval hints for BLE clients.
  pAdvertising->setMinPreferred(0x12);
  pAdvertising->setMinPreferred(0x02);
}

void bluetooth_service_start() {
  NimBLEDevice::startAdvertising();
}

void bluetooth_service_stop() {
  NimBLEDevice::stopAdvertising();
}
