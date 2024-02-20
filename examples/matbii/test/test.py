from star_ray_example_matbii import MATBIIEnvironment
import time
import ray

# from star_ray_example_matbii import MATBIIEnvironment

if __name__ == "__main__":
    try:

        ray.init()

        env = MATBIIEnvironment()
        running = True
        while running:
            time.sleep(0.1)
            # start_time = time.time()
            running = env.step()
            # end_time = time.time()
            # elapsed_time = end_time - start_time
            # print(f"The function took {elapsed_time} seconds to complete.")
    except Exception as e:
        raise e
    finally:
        print("SHUTTING DOWN")
        env.close()
