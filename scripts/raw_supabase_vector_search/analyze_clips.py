import cv2
import numpy as np

def analyze_clip_3():
    cap = cv2.VideoCapture("clips/raw_supabase_vector_search/clip_03.mp4")
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Clip 3: FPS={fps}, Frames={total_frames}, Duration={total_frames/fps:.3f}s")
    
    # We want to check:
    # 1. Start frame: does it show OBS or VS Code?
    # 2. Terminal region: when does "Top Match: Tesla Model 3" appear?
    # Terminal text region is roughly y: [630:730], x: [40:400]
    # 3. End frame: when does OBS appear?
    
    # Check start
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ret, frame0 = cap.read()
    
    # Let's inspect frames around terminal execution
    # Terminal prompt is at roughly y in 660..700
    events = []
    prev_term = None
    
    for fn in range(0, total_frames, 6): # check every 0.1s
        cap.set(cv2.CAP_PROP_POS_FRAMES, fn)
        ret, frame = cap.read()
        if not ret:
            break
        t = fn / fps
        
        # Check if OBS is present: in OBS top-left title or big UI
        # In OBS frame, top bar has OBS title: y in [0:40], x in [0:300]
        # In VSCode, top bar has "File Edit Selection..."
        is_obs = False
        top_strip = frame[0:30, 0:200]
        # In OBS, background is dark grey ~ #2b2e38 (B=56, G=46, R=43)
        # In VSCode, top menu is #181818
        if np.mean(top_strip) > 50:
            is_obs = True
            
        # Terminal area (approx y: 640..750, x: 40..300)
        term_crop = frame[640:740, 40:300]
        
        events.append((fn, t, is_obs, np.mean(term_crop)))
    
    cap.release()
    return events

if __name__ == "__main__":
    events = analyze_clip_3()
    # Find start non-OBS
    obs_start = [e for e in events if e[2] and e[1] < 5.0]
    obs_end = [e for e in events if e[2] and e[1] > 20.0]
    print(f"OBS at start: {obs_start[0][1] if obs_start else 'None'} to {obs_start[-1][1] if obs_start else 'None'}")
    print(f"OBS at end starts at: {obs_end[0][1] if obs_end else 'None'}")
