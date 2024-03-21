import signal
import sys
import time


def sigint_handler(signum, frame):
    print("Received SIGINT (Ctrl+C)")
    sys.exit(0)


def sigterm_handler(signum, frame):
    print("Received SIGTERM")
    sys.exit(0)


def main():
    # Register signal handlers
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    print(
        "Signal test script running. Press Ctrl+C to send SIGINT or use 'kill -TERM <pid>' to send SIGTERM."
    )

    # Keep the script running indefinitely
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main()
