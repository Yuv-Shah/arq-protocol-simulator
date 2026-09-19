# ARQ Protocol Simulator

An interactive simulator for **Go-Back-N (GBN)** and **Selective Repeat (SR) ARQ** protocols. The project demonstrates packet transmission, packet loss, acknowledgments, timeouts, retransmission, and error recovery through animated frame transitions.

## Overview

Automatic Repeat reQuest (ARQ) protocols provide reliable data transmission over unreliable networks by detecting lost or corrupted frames and retransmitting them.

This simulator visually demonstrates the difference between:

* **Go-Back-N ARQ**: Retransmits the lost frame and all subsequent frames in the current transmission window.
* **Selective Repeat ARQ**: Retransmits only the specific frames that were lost or corrupted while buffering correctly received out-of-order frames.

The simulator is designed as an educational tool for understanding reliable data transfer and sliding-window ARQ protocols.

## Features

* Go-Back-N ARQ simulation
* Selective Repeat ARQ simulation
* Configurable number of frames
* Configurable sliding-window size
* Configurable packet-loss probability
* Simulated acknowledgments
* Timeout detection
* Frame retransmission
* Packet loss visualization
* Animated frame transitions
* Step-by-step simulation
* Simulation statistics
* Comparison of GBN and Selective Repeat behavior

## How It Works

The simulator consists of three main components:

```text
Sender
   │
   │ Frames
   ▼
Network
   │
   │ Packet Loss / Transmission
   ▼
Receiver
   │
   │ ACK
   └──────────────────► Sender
```

The simulated network introduces packet loss according to the configured loss probability.

When a frame is lost, the sender detects the missing acknowledgment through a timeout and retransmits frames according to the selected ARQ protocol.

### Go-Back-N

In Go-Back-N, if a frame is lost, subsequent out-of-order frames are discarded by the receiver.

```text
Frame 0 ─────────► Received
Frame 1 ─────────► Received
Frame 2 ─────────► LOST
Frame 3 ─────────► Discarded
Frame 4 ─────────► Discarded

Timeout for Frame 2

Frame 2 ─────────► Retransmitted
Frame 3 ─────────► Retransmitted
Frame 4 ─────────► Retransmitted
```

### Selective Repeat

In Selective Repeat, correctly received out-of-order frames are buffered by the receiver.

```text
Frame 0 ─────────► Received
Frame 1 ─────────► Received
Frame 2 ─────────► LOST
Frame 3 ─────────► Buffered
Frame 4 ─────────► Buffered

Timeout for Frame 2

Frame 2 ─────────► Retransmitted

Frames 2, 3, 4
       │
       ▼
Delivered in order
```

This difference is the primary behavior demonstrated by the simulator.

## Prerequisites

Before installing the project, make sure the following software is installed.

### Python

**Python 3.10 or newer** is recommended.

Check your Python installation:

```bash
python --version
```

On some Linux/macOS systems:

```bash
python3 --version
```

### Git

Git is required to clone and manage the repository.

Check your Git installation:

```bash
git --version
```

### Recommended

A Python virtual environment is recommended to keep project dependencies isolated.

The project requires a system capable of running Python and its GUI dependencies.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Yuv-Shah/arq-protocol-simulator.git
```

Navigate into the project directory:

```bash
cd arq-protocol-simulator
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
```

Linux/macOS:

```bash
python3 -m venv .venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 4. Upgrade pip

```bash
python -m pip install --upgrade pip
```

### 5. Install project dependencies

```bash
pip install -r requirements.txt
```

## Running the Project

After completing the installation, run:

```bash
python main.py
```

The simulator will launch with the available protocol and simulation controls.


## Technologies

* Python
* Object-Oriented Programming
* Go-Back-N ARQ
* Selective Repeat ARQ
* Sliding Window Protocols
* Event-driven simulation
* GUI-based visualization

## Simulation Parameters

| Parameter        | Description                                  |
| ---------------- | -------------------------------------------- |
| Number of Frames | Total number of frames generated             |
| Window Size      | Maximum number of unacknowledged frames      |
| Packet Loss      | Probability that a transmitted frame is lost |
| Protocol         | Go-Back-N or Selective Repeat                |
| Animation Speed  | Controls the speed of frame transitions      |

## Statistics

During a simulation, the system records metrics such as:

* Total frames transmitted
* Number of lost frames
* Number of retransmissions
* Number of acknowledgments
* Successfully delivered frames
* Protocol overhead
* Transmission efficiency

These statistics can be used to compare the behavior of Go-Back-N and Selective Repeat under different network conditions.

## Example Experiment

A sample experiment can use:

```text
Frames:       20
Window Size:   4
Packet Loss:  20%
```

Run the experiment using Go-Back-N and then Selective Repeat with the same parameters.

The resulting retransmission count and transmission efficiency can then be compared to observe how the two protocols respond to packet loss.

## Learning Objectives

This project demonstrates:

1. Reliable data transmission over an unreliable channel
2. Sliding-window protocols
3. Sequence numbers
4. Acknowledgments
5. Timeouts
6. Packet loss
7. Retransmission
8. Receiver buffering
9. Go-Back-N behavior
10. Selective Repeat behavior

## Future Improvements

Possible extensions include:

* Corrupted-frame simulation
* Configurable timeout values
* Duplicate ACK handling
* Fast retransmission
* Throughput graphs
* Automated GBN vs SR experiments
* Real-time performance comparison
* Exporting simulation results
* Additional ARQ protocols

## License

This project is intended for educational and academic purposes.
