import carla
import time

def main():
    # Conexión a CARLA
    client = carla.Client('localhost', 2000)
    client.set_timeout(5.0)

    world = client.get_world()
    spectator = world.get_spectator()

    print("Mostrando posición y rotación del spectator (Ctrl+C para salir):\n")

    try:
        while True:
            transform = spectator.get_transform()
            loc = transform.location
            rot = transform.rotation

            # Posición (x,y,z) y orientación (pitch,yaw,roll)
            print(
                f"Posición -> x={loc.x:.2f}, y={loc.y:.2f}, z={loc.z:.2f} | "
                f"Rotación -> pitch={rot.pitch:.2f}, yaw={rot.yaw:.2f}, roll={rot.roll:.2f}",
                end="\r",  # sobrescribe en una sola línea
            )

            time.sleep(0.1)  # refresco cada 100 ms
    except KeyboardInterrupt:
        print("\nFinalizado.")

if __name__ == "__main__":
    main()
