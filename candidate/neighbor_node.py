#Author: Christopher Teggatz
#Date: 9/12/2025
#This should be the only file you edit. You are free to look at other files for reference, but do not change them.
#Below are are two methods which you must implement: euclidean_dist_to_origin and nearest_neighbor as well as the main function beacon handling. 
#Helper Functions are allowed, but not required. You must not change the imports, the main function signature, or the return value of the main function.


"""
Neighbor Table

Listen on UDP 127.0.0.1:5005 for beacon messages:
  {"id":"veh_XXX","pos":[x,y],"speed":mps,"ts":epoch_ms}

Collect beacons for ~1 second starting from the *first* message.
Then print exactly ONE JSON line and exit:

{
  "topic": "/v2x/neighbor_summary",
  "count": <int>,
  "nearest": {"id": "...", "dist": <float>} OR null,
  "ts": <now_ms>
}

Constraints:
- Python 3 stdlib only.
- Ignore malformed messages; don’t crash.
- Do NOT listen to ticks (5006).
"""

import socket, json, time, math, sys
from typing import Dict, Any, Optional, Tuple

HOST = "127.0.0.1"
PORT_BEACON = 5005
COLLECT_WINDOW_MS = 1000  # ~1 second

# enable print statements for debuging purposes...
DEBUG = False

def now_ms() -> int:
    return int(time.time() * 1000)

def euclidean_dist_to_origin(pos) -> float:
    # just do a basic magnitude formula 
    return math.trunc(
        float(
            math.sqrt(
                math.pow(pos[0],2) +math.pow(pos[1],2)
            )
        ) * 100 #Set to 3 sigfigs cause thats what examples show
    ) / 100

def nearest_neighbor(neighbors: Dict[str, Dict[str, Any]]) -> Optional[Tuple[str, float]]:
    # neighbors[id] -> {"pos":[x,y], "speed": float, "last_ts": int}
    # TODO: iterate neighbors, compute min distance, return (id, dist) or None
    
    # go through the neighbors, identify smallest, return it
    min = None
    for key, values in neighbors.items():
        neighbor = (key, euclidean_dist_to_origin(values['pos']))
        # if there is no min just set it to the currect
        if(min == None):
            min = neighbor
        # if the min is larger dist, replace it 
        elif(min[1] > neighbor[1]):
            min = neighbor
    # return the result of this
    return min

# function that makes sure the messages are in a correct order to be added
def validate_message(msg: Dict[str, Any]) -> bool:
    
    if not isinstance(msg, dict):
        debug_print(f"not a dictionary -> {msg}")
        return False
            
    # validate the id
    if not isinstance(msg["id"], str):
        debug_print(f"id is not a string -> {msg['id']}")
        return False
    
    # validate the list of positions
    if not isinstance(msg["pos"], list):
        debug_print(f"pos is not list -> {msg['pos']}")
        return False
    # if not length two then not operating in 2d
    if len(msg["pos"]) != 2:
        debug_print(f"pos list contains more then 2 values! -> {msg['pos']}")
        return False
    # make sure the contents are floats / ints
    for item in msg["pos"]:
        if not isinstance(item, (float, int)):
            debug_print(f"pos list contains non number -> {msg['pos']}")
            return False
    
    # validate the speed
    if not isinstance(msg["speed"], (float, int)):
        debug_print("speed is not a number!")
        return False
    # speed is a scalar value? so no negatives
    if msg["speed"] < 0:
        debug_print(f"speed is scalar, it cant be less then zero -> {msg['ts']}")
        return False
    
    #validate last tick
    if not isinstance(msg["ts"], int):
        debug_print(f"tick is not a number -> {msg['ts']}")
        return False
    
    # if all tests pass then return true
    return True

# print wrapper for debugging...
def debug_print(msg: str):
    if(DEBUG):
        print(msg)


def main() -> int:
    neighbors: Dict[str, Dict[str, Any]] = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT_BEACON))
    sock.settimeout(1.5) 

    first_ts: Optional[int] = None
    try:
        while True:
            try:
                data, _ = sock.recvfrom(4096)
            except socket.timeout:
                break  

            try:
                msg = json.loads(data.decode("utf-8"))
            except json.JSONDecodeError:
                continue  
            
            # Expect: {"id": "...", "pos":[x,y], "speed": float, "ts": int}
            # TODO: validate required keys/types defensively
            # If valid:
            #   neighbors[msg["id"]] = {"pos": msg["pos"], "speed": msg["speed"], "last_ts": msg["ts"]}
            #hint: beacon handling, check each message and store in neighbors, try to cover edge cases
            # try to avoid changing anything in the main function outside this TODO block
            
            
            # validate the message to make sure correct format
            if not validate_message(msg = msg):
                continue

            # if types are valid continue and parse
            debug_print(f'PYTHON - recieved {msg} from {_}')
            neighbors[msg['id']] = {
                "pos" : msg['pos'],
                "speed" : msg['speed'],
                "last_ts" : msg["ts"]
            }
            
            


            #END of TODO block
            now = now_ms()
            if first_ts is None:
                first_ts = now
            # stop after ~1 second from first message
            if first_ts is not None and (now - first_ts) >= COLLECT_WINDOW_MS:
                break

    finally:
        sock.close()

    # Build summary
    nn = nearest_neighbor(neighbors)
    summary = {
        "topic": "/v2x/neighbor_summary",
        "count": len(neighbors),
        "nearest": None if nn is None else {"id": nn[0], "dist": nn[1]},
        "ts": now_ms(),
    }
    print(json.dumps(summary), flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
