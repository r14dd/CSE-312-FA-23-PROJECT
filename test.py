from threading import Timer

def timeout():
    print("Game over")

# duration is in seconds
t = Timer(20 * 60, timeout)
t.start()

print(t)

# wait for time completion
t.join()