// Cargo.toml dependencies:
// [dependencies]
// btleplug = { version = "0.11", features = ["tokio"] }
// tokio = { version = "1", features = ["full"] }
// uuid = "1.3"

use btleplug::api::{Central, CentralEvent, Characteristic, Manager as _, Peripheral as _, ScanFilter, ValueNotification, WriteType, UUID};
use btleplug::platform::{Adapter, Manager, Peripheral};
use std::collections::HashMap;
use std::error::Error;
use std::fs::OpenOptions;
use std::io::Write;
use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::sync::Mutex;
use tokio::time;

const SERVICE_UUID: &str = "19b10000-e8f2-537e-4f6c-d104768a1214";
const CHARACTERISTIC_UUID: &str = "19b10001-e8f2-537e-4f6c-d104768a1214";
const SAMPLE_SIZE: usize = 6; // AccelX, Y, Z, GyroX, Y, Z
const SAMPLES_PER_BATCH: usize = 6;

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let manager = Manager::new().await?;
    let adapters = manager.adapters().await?;

    if adapters.is_empty() {
        eprintln!("No BLE adapters found");
        return Ok(());
    }

    let adapter = adapters.into_iter().nth(0).unwrap();
    println!("Using adapter: {}", adapter.adapter_info().await?);

    let discovered = Arc::new(Mutex::new(HashMap::new()));
    let discovered_clone = discovered.clone();

    adapter.start_scan(ScanFilter::default()).await?;
    println!("Scanning for devices...");

    let mut events = adapter.events().await?;
    tokio::spawn(async move {
        while let Some(event) = events.recv().await {
            if let CentralEvent::DeviceDiscovered(id) = event {
                let peripheral = adapter.peripheral(&id).await.unwrap();
                if let Some(name) = peripheral.properties().await.unwrap().local_name {
                    if name == "IMU_BLE_Device" {
                        println!("Discovered: {}", peripheral.address());
                        discovered_clone.lock().await.insert(peripheral.address().to_string(), peripheral);
                    }
                }
            }
        }
    });

    time::sleep(Duration::from_secs(5)).await;
    adapter.stop_scan().await?;

    let devices = discovered.lock().await;
    let mut handles = vec![];

    for (addr, peripheral) in devices.iter() {
        let p = peripheral.clone();
        let a = addr.clone();
        let handle = tokio::spawn(async move {
            if let Err(e) = handle_device(p, a).await {
                eprintln!("[{}] Error: {}", addr, e);
            }
        });
        handles.push(handle);
        time::sleep(Duration::from_secs(2)).await; // stagger connection
    }

    for h in handles {
        h.await?;
    }

    Ok(())
}

async fn handle_device(peripheral: Peripheral, addr: String) -> Result<(), Box<dyn Error>> {
    peripheral.connect().await?;
    peripheral.discover_services().await?;

    let chars = peripheral.characteristics();
    let characteristic = chars.iter()
        .find(|c| c.uuid == UUID::parse_str(CHARACTERISTIC_UUID).unwrap())
        .ok_or("Notify characteristic not found")?
        .clone();

    println!("[{}] Connected, subscribing to notifications...", addr);

    let path = format!("dataset/imu_data/{}.csv", addr.replace(":", "_"));
    let file = Arc::new(Mutex::new(OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)?));

    {
        let mut f = file.lock().await;
        writeln!(f, "Timestamp,AccelX,AccelY,AccelZ,GyroX,GyroY,GyroZ")?;
    }

    let file_clone = file.clone();
    peripheral.on_notification(Box::new(move |data: ValueNotification| {
        let file = file_clone.clone();
        Box::pin(async move {
            let payload = &data.value;
            if payload.len() != SAMPLES_PER_BATCH * SAMPLE_SIZE * 4 {
                eprintln!("Invalid payload size: {}", payload.len());
                return;
            }

            let mut samples = vec![];
            for chunk in payload.chunks_exact(4) {
                let val = f32::from_le_bytes(chunk.try_into().unwrap());
                samples.push(val);
            }

            let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs_f64();
            let dt = 0.02;
            let mut f = file.lock().await;
            for i in 0..SAMPLES_PER_BATCH {
                let timestamp = now - dt * (SAMPLES_PER_BATCH as f64 - 1.0 - i as f64);
                let line: Vec<String> = std::iter::once(timestamp.to_string())
                    .chain(samples[i * SAMPLE_SIZE..(i + 1) * SAMPLE_SIZE].iter().map(|f| f.to_string()))
                    .collect();
                writeln!(f, "{}", line.join(",")).ok();
            }
        })
    })).await;

    peripheral.subscribe(&characteristic).await?;
    println!("[{}] Subscribed.", addr);

    // Wait forever (or until externally killed)
    loop {
        time::sleep(Duration::from_secs(1)).await;
    }
}
