
# A probabilistic reversal learning task in which the subject must initiate
# the trial in the center poke, then chose poke_a or poke_b for a probabilistic
# reward.  The reward probabilities on the poke_a and poke_b side reverse from
# time to time.

from pyControl.utility import *
import hardware_definition as hw

#-------------------------------------------------------------------------
# States and events.
#-------------------------------------------------------------------------

states = ['init_trial',
          'choice_state',
          'poke_a_reward',
          'poke_b_reward',
          'sound_a_reward',
          'sound_b_reward',
          'sound_a_no_reward',
          'sound_b_no_reward',
          'inter_trial_interval',
          'period_before_iti',
          'free_reward_trial',
          'a_forced_state', 'b_forced_state','start_state']

events = ['poke_1',
          'poke_2',
          'poke_3',
          'poke_4',
          'poke_5',
          'poke_6',
          'poke_1_out',
          'poke_2_out',
          'poke_3_out',
          'poke_4_out',
          'poke_5_out',
          'poke_6_out',
          'session_timer',
          'reward_consumption_timer',
          'old_task','new_task']

initial_state = 'start_state'

#-------------------------------------------------------------------------
# Variables.
#-------------------------------------------------------------------------

# Parameters
v.reward_a_available = 1 # Number of rewards from A poke 
v.reward_b_available = 1 # Number of rewards from B poke 
v.forced_trial = 0 # Forced or free trial (0 free, 1 forced)
v.new_task = 1
v.choice = 0 # Initiate choice at 0
v.session_duration = 0.5*hour
v.reward_durations = [93,93] # Reward delivery duration (ms) [a, b]
v.ITI_duration = 1.75*second # Inter trial interval duration.
v.state = withprob(0.5) # Which side is currently good: True: a, False: b
v.reward_probs = {'good': 0.8, 'bad':0.2} # Reward probabilities on the good/bad side.
v.threshold=0.75 #Threshold for crossing the reversal
v.trials_post_threshold = [5,15] #Range of the number of trials after the threshold has passed before the reversal
v.sound_duration=250*ms
v.repoke_window = 250*ms #Time window where an animal can re-poke during the trial 
v.poke_map = {'poke_i': 1, # Trial initiation poke number.
              'poke_a': 5, # Choice poke A poke number
              'poke_b': 3} # Choice poke B poke number.

# Variable
v.n_rewards = 0 # Number of rewards obtained.
v.n_trials = 0 # Number of trials recieved.
v.correct_mov_ave = exp_mov_ave(tau=8, init_value=0.5)
v.correct=0 #Correct vs. Incorrect Choice (1-correct; 0-incorrect)
v.outcome=0 #Rewarded or not (1-rewarded; 0 - non-rewarded)
v.block_number=0 #Number of rewersals
v.trials_till_reversal=0 #Number of trials after the threshold before the reversal
v.threshold_crossed=False
v.cumulative_reversals = 0
v.prev_session_poke_i = None 
v.trial_type = sample_without_replacement(['forced', 'free', 'free', 'free'])
v.forced_choice_trial = sample_without_replacement(['a','b' ])

def set_reward_probs():
    # Set reward probabilities dependent on number of reversals in current task.
    if v.cumulative_reversals < 3:
        v.reward_probs = {'good': 0.9, 'bad':0.1}
    elif v.cumulative_reversals < 5:
        v.reward_probs = {'good': 0.85, 'bad':0.15}    
    else:
        v.reward_probs = {'good': 0.8, 'bad':0.2}  

#-------------------------------------------------------------------------        
# Define behaviour.
#-------------------------------------------------------------------------

# Run start and stop behaviour.

def run_start(): 
    # Set session timer and turn on houslight.
    set_timer('session_timer', v.session_duration)  
    hw.houselight.on()
    # Set pokes used for initiation and choice from poke_map dictionary.
    poke_dict = {1: hw.poke_1,
                 2: hw.poke_2,
                 3: hw.poke_3,
                 4: hw.poke_4,
                 5: hw.poke_5,
                 6: hw.poke_6} 
    hw.poke_i = poke_dict[v.poke_map['poke_i']]
    hw.poke_a = poke_dict[v.poke_map['poke_a']]
    hw.poke_b = poke_dict[v.poke_map['poke_b']]
    hw.poke_a.SOL = hw.SOL_B
    hw.poke_b.SOL = hw.SOL_A
    v.poke_i = v.poke_map['poke_i'] # Poke I in the current session
    if  v.poke_i != v.prev_session_poke_i:
        v.new_task = 1
        v.cumulative_reversals = 0 # Configuration changed 
    elif v.poke_i == v.prev_session_poke_i:
        v.new_task = 0 
    set_reward_probs()

def start_state(event):
    if event == 'entry':
        if v.new_task == 1:
            set_timer('new_task',0)# If new task set initial state to 'check_if_free_rewarded_trial'
        elif v.new_task == 0:
            set_timer('old_task',0)
    if event == 'new_task':
        goto_state('free_reward_trial')
    elif event == 'old_task':
        goto_state('init_trial')

#Free rewards to deliver on each new task from A and B oikes 
def free_reward_trial(event):
    #Turn on both reward ports
    if event == 'entry':
        print('FR#{}'.format(v.reward_b_available + v.reward_a_available)) 
        if (v.reward_a_available != 0 and v.reward_b_available != 0):
            hw.poke_a.LED.on()
            hw.poke_b.LED.on()
        elif v.reward_a_available != 0:
            hw.poke_a.LED.on()
        elif v.reward_b_available != 0:
            hw.poke_b.LED.on()
    elif event == hw.poke_a.input.rising_event: 
        if  v.reward_a_available != 0: #free reward a consumed 
            goto_state('sound_a_reward')
            v.reward_a_available -= 1
    elif event == hw.poke_b.input.rising_event:
        if v.reward_b_available != 0:
            goto_state('sound_b_reward')
            v.reward_b_available -= 1
    elif event == 'exit':
        hw.poke_a.LED.off()
        hw.poke_b.LED.off()

def run_end():
    # Turn off all hardware outputs.  
    v.prev_session_poke_i = v.poke_i
    hw.off()

# State behaviour functions.
def init_trial(event):
    # Turn on center Poke LED and wait for center poke.
    v.forced_trial = 0 
    if event == 'entry':
      hw.poke_i.LED.on()
    elif event == 'exit':
        hw.poke_i.LED.off()
    elif event == hw.poke_i.input.rising_event:
        #hw.speaker.set_volume(25)
        hw.speaker.click()
        if v.trial_type.next() == 'free': 
            goto_state('choice_state')
        else: #forced_choice_trial':
            if v.forced_choice_trial.next() == 'a':
                goto_state('a_forced_state')
            else:
                goto_state('b_forced_state')

def a_forced_state(event):
    if event == 'entry':
        hw.poke_a.LED.on()
    elif event == hw.poke_a.input.rising_event:
        v.forced_trial = 1 
        if v.state: 
            reward_prob = v.reward_probs['good']
        else:
            reward_prob = v.reward_probs['bad']
        if  withprob(reward_prob):
            goto_state('sound_a_reward')
        else:
            v.outcome = 0
            goto_state('sound_a_no_reward')
    elif event == 'exit':
        hw.poke_a.LED.off()

def b_forced_state(event):
    if event == 'entry':
        hw.poke_b.LED.on()
    elif event == hw.poke_b.input.rising_event:
        v.forced_trial = 1 
        if not v.state: 
            reward_prob = v.reward_probs['good']
        else:
            reward_prob = v.reward_probs['bad']
        if  withprob(reward_prob):
            goto_state('sound_b_reward')
        else:
            v.outcome = 0
            goto_state('sound_b_no_reward')
    elif event == 'exit':
        hw.poke_b.LED.off()


def choice_state(event):
    # Wait for left or right choice and evaluate if reward is delivered.
    if event == 'entry':
        hw.poke_a.LED.on()
        hw.poke_b.LED.on()
    elif event == 'exit':
        hw.poke_a.LED.off()
        hw.poke_b.LED.off()
    elif event == hw.poke_a.input.rising_event:
        v.choice = 1
        if v.state: # correct choice
            reward_prob = v.reward_probs['good']
            v.correct=1
            v.correct_mov_ave.update(1)
        else:
            reward_prob = v.reward_probs['bad']
            v.correct=0
            v.correct_mov_ave.update(0)
        if  withprob(reward_prob):
            goto_state('sound_a_reward')
        else:
            v.outcome=0
            goto_state('sound_a_no_reward')
    elif event == hw.poke_b.input.rising_event:
        v.choice = 0
        if not v.state:
            reward_prob= v.reward_probs['good']
            v.correct=1
            v.correct_mov_ave.update(1)
        else:
            reward_prob = v.reward_probs['bad']
            v.correct=0
            v.correct_mov_ave.update(0)
        if  withprob(reward_prob):
            goto_state('sound_b_reward')
        else:
            v.outcome=0
            goto_state('sound_b_no_reward')
     
def sound_a_no_reward(event):
    if event=='entry':
        timed_goto_state('period_before_iti', v.sound_duration)
        #hw.speaker.set_volume(25)
        hw.speaker.noise()
    elif event=='exit':
        hw.speaker.off()     

def sound_b_no_reward(event):
    if event=='entry':
        timed_goto_state('period_before_iti', v.sound_duration)
        #hw.speaker.set_volume(25)
        hw.speaker.noise()
    elif event=='exit':
        hw.speaker.off()

def sound_a_reward(event):
    if event == 'entry':
        timed_goto_state('poke_a_reward', v.sound_duration)
        #hw.speaker.set_volume(6)
        hw.speaker.sine(5000) #Play white noise for non-rewarded trial 
    if event=='exit':
        hw.speaker.off()

def sound_b_reward(event):
    if event == 'entry':
        timed_goto_state('poke_b_reward', v.sound_duration)
        #hw.speaker.set_volume(6)
        hw.speaker.sine(5000)
    if event=='exit':
        hw.speaker.off()

def poke_a_reward(event):
    # Deliver reward to left poke, increment reward counter.
    if event=='entry': #Play sine wave of 5kHz for a rewarded trial 
        timed_goto_state('period_before_iti', v.reward_durations[0])
        hw.poke_a.SOL.on()
        v.n_rewards += 1
        v.outcome=1
    elif event == 'exit':
        hw.poke_a.SOL.off()

def poke_b_reward(event):
    # Deliver reward to right poke, increment reward counter.
    if event=='entry':
        timed_goto_state('period_before_iti', v.reward_durations[1])
        hw.poke_b.SOL.on()
        v.n_rewards += 1
        v.outcome=1
    elif event == 'exit':
        hw.poke_b.SOL.off() 

def period_before_iti(event): # monitor re-poking events to set the intertrial interval after the animal does not poke for v.repoke_window
    if event == 'entry':
        if not (hw.poke_a.value() or hw.poke_b.value()): # Subject already left poke.
            set_timer('reward_consumption_timer', v.repoke_window)
    if (event == hw.poke_a.input.falling_event) or (event == hw.poke_b.input.falling_event):
        set_timer('reward_consumption_timer', v.repoke_window)
    elif (event == hw.poke_a.input.rising_event) or (event == hw.poke_b.input.rising_event):
        disarm_timer('reward_consumption_timer')
    elif (event =='reward_consumption_timer'):
        if (v.reward_a_available != 0 or v.reward_b_available != 0):
            goto_state('free_reward_trial')
        elif (v.reward_a_available == 0 or v.reward_b_available == 0):
            goto_state('init_trial')
        else:
            goto_state('inter_trial_interval')

def inter_trial_interval(event):
    # Increment trial counter, check for reversal transition.
    if event == 'entry':
        timed_goto_state('init_trial', v.ITI_duration)
        v.n_trials += 1
        print('T#:{}, R#:{}, B#:{}, S:{}, C:{}, O:{}, Cave:{:.3}, Count:{}, Poke_IAB: {}{}{},RP:{}, FT:{}'.format(
              v.n_trials, v.n_rewards,v.block_number, int(v.state), v.choice, v.outcome,v.correct_mov_ave.value,
              v.trials_till_reversal, v.poke_map['poke_i'], v.poke_map['poke_a'], v.poke_map['poke_b'], v.reward_probs, v.forced_trial)) #T-trials, R-rewards, B-reversals, S-state(1: left good, 0:right good)
        if v.threshold_crossed: # Threshold crossed on earlier trial.
            v.trials_till_reversal = v.trials_till_reversal - 1
            if v.trials_till_reversal == 0: # Reversal
                v.cumulative_reversals +=1
                v.block_number+=1
                v.threshold_crossed = False
                v.state = not v.state # Reversal has occured.
                v.correct_mov_ave.value = 1 - v.correct_mov_ave.value
                set_reward_probs()
        elif v.correct_mov_ave.value > v.threshold: #Threshold crossed on this trial.
            v.threshold_crossed=True
            v.trials_till_reversal = randint(v.trials_post_threshold[0],v.trials_post_threshold[1])

# State independent behaviour.
def all_states(event):
    # When 'session_timer' event occurs stop framework to end session.
    if event == 'session_timer':
        stop_framework()