import Foundation
import CoreBluetooth
import Dispatch

let baseTrialDir = FileManager.default.currentDirectoryPath + "/dataset/imu_data"
var loggingEnabled = false

class SensorHandler: NSObject, CBPeripheralDelegate {
    let peripheral: CBPeripheral
    let queue: DispatchQueue
    var logFile: FileHandle?
    var logPath: String = ""
    var charUUID: CBUUID?
    var controlCharUUID: CBUUID?

    init(peripheral: CBPeripheral, trialPath: String) {
        self.peripheral = peripheral
        self.queue = DispatchQueue(label: "decode_queue_\(peripheral.identifier.uuidString)")
        super.init()
        peripheral.delegate = self
        createCSV(trialPath: trialPath)
    }

    func createCSV(trialPath: String) {
        let filename = peripheral.identifier.uuidString.replacingOccurrences(of: "-", with: "_") + ".csv"
        logPath = trialPath + "/" + filename
        FileManager.default.createFile(atPath: logPath, contents: nil)
        if let handle = try? FileHandle(forWritingTo: URL(fileURLWithPath: logPath)) {
            logFile = handle
            handle.write("Millis,AccelX,AccelY,AccelZ,GyroX,GyroY,GyroZ\n".data(using: .utf8)!)
            print("📁 Logging to: \(logPath)")
        } else {
            print("❌ Failed to open log file for \(peripheral.identifier)")
        }
    }

    func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        for service in peripheral.services ?? [] {
            peripheral.discoverCharacteristics(nil, for: service)
        }
    }

    func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        for char in service.characteristics ?? [] {
            if char.properties.contains(.notify) {
                charUUID = char.uuid
                peripheral.setNotifyValue(true, for: char)
                print("📡 Subscribed to \(char.uuid) on \(peripheral.identifier)")
            } else if char.properties.contains(.write) {
                controlCharUUID = char.uuid
                print("📝 Found control characteristic: \(char.uuid)")
            }
        }
    }

    func sendRecordingSignal() {
        guard let controlUUID = controlCharUUID else { return }
        guard let controlChar = (peripheral.services?.flatMap { $0.characteristics ?? [] }.first { $0.uuid == controlUUID }) else { return }
        let value: [UInt8] = [1]
        peripheral.writeValue(Data(value), for: controlChar, type: .withResponse)
        print("📤 Sent start recording signal to \(peripheral.identifier)")
    }

    func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic, error: Error?) {
        guard loggingEnabled else { return }
        guard let data = characteristic.value else { return }

        queue.async {
            guard data.count % 28 == 0 else {
                print("⚠️ Packet size mismatch (\(data.count) bytes) from \(peripheral.identifier)")
                return
            }
            guard let handle = self.logFile else { return }

            let floatsPerSample = 6
            let sampleSize = 4 + (floatsPerSample * 4)
            let sampleCount = data.count / sampleSize

            for i in 0..<sampleCount {
                let offset = i * sampleSize

                // Decode timestamp (uint32_t millis)
                let timestamp: UInt32 = data.withUnsafeBytes {
                    $0.load(fromByteOffset: offset, as: UInt32.self)
                }

                // Decode float data
                let floatOffset = offset + 4
                let floats: [Float] = data.withUnsafeBytes {
                    let base = $0.baseAddress!.advanced(by: floatOffset)
                    return Array(UnsafeBufferPointer(start: base.assumingMemoryBound(to: Float.self), count: floatsPerSample))
                }

                let row = [String(timestamp)] + floats.map { String(format: "%.3f", $0) }
                if let line = row.joined(separator: ",").appending("\n").data(using: .utf8) {
                    handle.write(line)
                }
            }
        }
    }
}


class BLELogger: NSObject, CBCentralManagerDelegate {
    var centralManager: CBCentralManager!
    var handlers: [UUID: SensorHandler] = [:]
    var scanTimer: DispatchSourceTimer?
    var trialPath: String = ""

    override init() {
        super.init()
        createTrialFolder()
        startKeyListener()
        centralManager = CBCentralManager(delegate: self, queue: nil)
    }

    func createTrialFolder() {
        let fm = FileManager.default
        try? fm.createDirectory(atPath: baseTrialDir, withIntermediateDirectories: true)
        let trialDirs = (try? fm.contentsOfDirectory(atPath: baseTrialDir)) ?? []
        let trialNumbers = trialDirs.compactMap { Int($0.replacingOccurrences(of: "trial_", with: "")) }
        let nextTrial = (trialNumbers.max() ?? 0) + 1
        trialPath = baseTrialDir + "/trial_\(nextTrial)"
        try? fm.createDirectory(atPath: trialPath, withIntermediateDirectories: true)
        print("📂 Created trial folder: \(trialPath)")
    }

    func startKeyListener() {
        DispatchQueue.global().async {
            while true {
                if let input = readLine(strippingNewline: true), input.lowercased() == "r" {
                    loggingEnabled = true
                    print("🟢 Logging started")
                    for handler in self.handlers.values {
                        handler.sendRecordingSignal()
                    }
                    break
                }
            }
        }
    }

    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        if central.state == .poweredOn {
            print("🔍 Scanning for IMU_BLE_Device...")
            central.scanForPeripherals(withServices: nil, options: nil)

            scanTimer = DispatchSource.makeTimerSource(queue: DispatchQueue.global())
            scanTimer?.schedule(deadline: .now() + 5.0)
            scanTimer?.setEventHandler { [weak self] in
                self?.centralManager.stopScan()
                print("🛑 Stopped scanning after 5 seconds")
                self?.scanTimer?.cancel()
                self?.scanTimer = nil
            }
            scanTimer?.resume()
        } else {
            print("⚠️ Bluetooth not ready")
        }
    }

    func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral,
                        advertisementData: [String : Any], rssi RSSI: NSNumber) {
        guard handlers[peripheral.identifier] == nil else { return }
        if peripheral.name == "IMU_BLE_Device" || peripheral.name == "Arduino" {
            let handler = SensorHandler(peripheral: peripheral, trialPath: trialPath)
            handlers[peripheral.identifier] = handler
            central.connect(peripheral, options: nil)
        }
    }

    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        print("🔗 Connected to \(peripheral.identifier)")
        peripheral.discoverServices(nil)
    }
}

let logger = BLELogger()
dispatchMain()
