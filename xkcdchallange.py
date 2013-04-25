import skein
import time, random
from multiprocessing import Array, Value, Lock, cpu_count, Pool
from ctypes import c_double, c_int

TARGETSTR = '5b4da95f5fa08280fc9879df44f418c8f9f12ba424b7757de02bbdfbae0d4c4fd' + \
	'f9317c80cc5fe04c6429073466cf29706b8c25999ddd2f6540d4475cc977b87f4757be' + \
	'023f19b8f4035d7722886b78869826de916a79cf9c94cc79cd4347d24b567aa3e2390' + \
	'a573a373a48a5e676640c79cc70197e1c5e7f902fb53ca1858b6'

TARGET = int(TARGETSTR, 16)

#variables shared between all processes
process_array = Array(c_double, cpu_count(), lock=Lock())
high_value = Value(c_int, 1024)

def run_worker():
    #method of naming each thread individually
    time.sleep(random.random()*cpu_count()) #reduces chance of two processes claiming the same id
    count =0
    for item in process_array:
        if item==0:
            #local_id is this threads process id
            local_id = count
        count +=1
    process_array[local_id] = 1
    
    best = high_value.value
    
    guess = random.getrandbits(128)
    start_time = time.time()
    
    i = 1
    
    while True:
	
	#the meat of the loop
        encoded = hex(guess)[2:].encode('ascii')
        digest = int(skein.skein1024(encoded).hexdigest(), 16)
        diff = bin(digest ^ TARGET).count('1')
	
        if diff < best:
            if diff < high_value.value:
                best = diff
                high_value.value = best
                print("pid:", local_id, "::", 'Found new best [%.3d]: \"%s\"' %(diff, encoded))
                
            if diff > high_value.value:
                best = high_value.value
                
        if i%500000==0:
            current_speed = i/(time.time()-start_time)
            process_array[local_id] = current_speed

        i += 1
        guess += 1

def main():
    cpus = cpu_count()
    pool = Pool(cpus)
    for i in range(cpus):
        pool.apply_async(run_worker)
    try:
        while True:
            time.sleep(15)
            pool_speed = 0
            for item in process_array:
                pool_speed += item
            print("Master :: Pool speed is", int(pool_speed), "hashes per second.")
            
    except KeyboardInterrupt:
        print('Terminating...')
        pool.terminate()
        pool.join()
    else:
        print('Quitting...')
        pool.close()
        pool.join()

if __name__ == "__main__":
    main()
