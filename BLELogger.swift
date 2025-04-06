// BLELogger.swift (Updated: Robust Logging & Float Decode Verification)

import Foundation
import CoreBluetooth
import Dispatch
import Darwin.C

let baseTrialDir = FileManager.default.currentDirectoryPath + "/dataset/imu_data"
var loggingEnabled = false

class SensorHandler: NSObject, CBPeripheralDelegate {
    let peripheral: CBPeripheral
    let queue: DispatchQueue
    var logFile: FileHandle?
    var logPath: String = ""
    var charUUID: CBUUID?

    init(peripheral: CBPeripheral, trialPath: String) {
        self.peripheral = peripheral
        self.queue = DispatchQueue(label: "queue_\(peripheral.identifier.uuidString)")
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
            handle.write("Timestamp,AccelX,AccelY,AccelZ,GyroX,GyroY,GyroZ\n".data(using: .utf8)!)
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
            }
        }
    }

    func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic, error: Error?) {
        guard loggingEnabled else { return }
        guard let data = characteristic.value else {
            print("⚠️ No data in characteristic update from \(peripheral.identifier)")
            return
        }

        let sampleSize = 6 * 4
        guard data.count % sampleSize == 0 else {
            print("❌ Unexpected packet size from \(peripheral.identifier): \(data.count) bytes")
            return
        }

        let sampleCount = data.count / sampleSize
        let floatsPerSample = 6

        guard let handle = logFile else {
            print("❌ Missing log file handle for \(peripheral.identifier)")
            return
        }

        queue.async {
            let now = Date().timeIntervalSince1970
            for i in 0..<sampleCount {
                let offset = i * floatsPerSample * 4
                let floats: [Float] = data.withUnsafeBytes {
                    let base = $0.baseAddress!.advanced(by: offset)
                    return Array(UnsafeBufferPointer(start: base.assumingMemoryBound(to: Float.self), count: floatsPerSample))
                }

                // Print full decoded data for debug
                // print("🧾 Sample \(i) from \(self.peripheral.identifier): \(floats)")

                let t = now - 0.02 * Double(sampleCount - 1 - i)
                let row = [String(format: "%.6f", t)] + floats.map { String(format: "%.3f", $0) }
                if let line = row.joined(separator: ",").appending("\n").data(using: .utf8) {
                    handle.write(line)
                } else {
                    print("⚠️ Failed to encode row for \(peripheral.identifier)")
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
