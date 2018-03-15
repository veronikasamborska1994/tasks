# A probabilistic reversal learning task in which the subject must initiate
# the trial in the center poke, then chose left or right for a probabilistic
# reward.  The reward probabilities on the left and right side reverse from
# time to time.

from pyControl.utility import *
import hardware_definition as hw

#-------------------------------------------------------------------------
# States and events.
#-------------------------------------------------------------------------

states = ['init_trial',
          'choice_state',
          'left_reward',
          'right_reward',
          'inter_trial_interval',
          'period_before_iti']

events = ['left_poke',
          'center_poke',
          'right_poke',
          'session_timer',
          'left_poke_out','right_poke_out','reward_consumption_timer']

initial_state = 'init_trial'

#-------------------------------------------------------------------------
# Variables.
#-------------------------------------------------------------------------

v.session_duration = 1*hour
v.reward_durations = [100,100] # Reward delivery duration (ms) [left, right]
v.ITI_duration = 1*second # Inter trial interval duration.
v.n_rewards = 0 # Number of rewards obtained.
v.n_trials = 0 # Number of trials recieved.
v.mean_block_length = 10 # Average block length between reversals.
v.state = withprob(0.5) # Which side is currently good: True: left, False: right
v.good_prob = 0.8 # Reward probabilities on the good side.
v.bad_prob  = 0.2 # Reward probabilities on the bad side.
v.correct_mov_ave = exp_mov_ave(tau=8, init_value=0.5)
v.threshold=0.6 #Threshold for crossing the reversal
v.correct=0 #Correct vs. Incorrect Choice (1-correct; 0-incorrect)
v.outcome=0 #Rewarded or not (1-rewarded; 0 - non-rewarded)
v.trials_post_threshold = [2,2] #Range of the number of trials after the threshold has passed before the reversal
v.block_number=0 #Number of rewersals
v.trials_till_reversal=0 #Number of trials after the threshold before the reversal
v.threshold_crossed=False
v.repoke_window = 250*ms #Time window where an animal can re-poke during the trial 


#-------------------------------------------------------------------------        
# Define behaviour.
#-------------------------------------------------------------------------

# Run start and stop behaviour.

def run_start(): 
    # Set session timer and turn on houslight.
    set_timer('session_timer', v.session_duration)  
    hw.houselight.on()                             
    
def run_end():
    # Turn off all hardware outputs.  
    hw.off()

# State behaviour functions.

def init_trial(event):
    # Turn on center Poke LED and wait for center poke.
    if event == 'entry':
        hw.center_poke.LED.on()
    elif event == 'exit':
        hw.center_poke.LED.off()
    elif event == 'center_poke':
        goto_state('choice_state')

def choice_state(event):
    # Wait for left or right choice and evaluate if reward is delivered.
    if event == 'entry':
        hw.left_poke.LED.on()
        hw.right_poke.LED.on()
    elif event == 'exit':
        hw.left_poke.LED.off()
        hw.right_poke.LED.off()
    elif event == 'left_poke':
        if v.state: # correct choice
            reward_prob = v.good_prob
            v.correct=1
            v.correct_mov_ave.update(1)
        else:
            reward_prob = v.bad_prob
            v.correct=0
            v.correct_mov_ave.update(0)
        if  withprob(reward_prob):
            goto_state('left_reward')
        else:
            v.outcome=0
            goto_state('period_before_iti')
    elif event == 'right_poke':
        if not v.state:
            reward_prob= v.good_prob
            v.correct=1
            v.correct_mov_ave.update(1)
        else:
            reward_prob = v.bad_prob
            v.correct=0
            v.correct_mov_ave.update(0)
        if  withprob(reward_prob):
            goto_state('right_reward')
        else:
            v.outcome=0
            goto_state('period_before_iti')
            

def left_reward(event):
    # Deliver reward to left poke, increment reward counter.
    if event == 'entry':
        timed_goto_state('period_before_iti', v.reward_durations[0])
        hw.left_poke.SOL.on()
        v.n_rewards += 1
        v.outcome=1
    elif event == 'exit':
        hw.left_poke.SOL.off()


def right_reward(event):
    # Deliver reward to right poke, increment reward counter.
    if event == 'entry':
        timed_goto_state('period_before_iti', v.reward_durations[1])
        hw.right_poke.SOL.on()
        v.n_rewards += 1
        v.outcome=1
    elif event == 'exit':
        hw.right_poke.SOL.off() 
       
def period_before_iti(event): # monitor re-poking events to set the intertrial interval after the animal does not poke for v.repoke_window
    if event == 'entry':
        if not (hw.left_poke.value() or hw.right_poke.value()): # Subject already left poke.
            set_timer('reward_consumption_timer', v.repoke_window)
    if (event=='left_poke_out') or (event=='right_poke_out'):
        set_timer('reward_consumption_timer', v.repoke_window)
    elif (event=='left_poke') or (event=='right_poke'):
        disarm_timer('reward_consumption_timer')
    elif (event=='reward_consumption_timer'):
        goto_state('inter_trial_interval')

def inter_trial_interval(event):
    # Increment trial counter, check for reversal transition.
    if event == 'entry':
        timed_goto_state('init_trial', v.ITI_duration)
        v.n_trials += 1
        print('T#:{}, R#:{}, B#:{}, S:{}, C:{}, O:{}, Cave:{:.3}, Count:{}'.format(v.n_trials, v.n_rewards,v.block_number, int(v.state), v.correct,
            v.outcome,v.correct_mov_ave.value, v.trials_till_reversal)) #T-trials, R-rewards, B-reversals, S-state(1: left good, 0:right good)
        if v.threshold_crossed: # Threshold crossed on earlier trial.
            v.trials_till_reversal = v.trials_till_reversal - 1
            if v.trials_till_reversal == 0: # Reversal
                print('Block transition')
                v.block_number+=1
                v.threshold_crossed = False
                v.state = not v.state # Reversal has occured.
                v.correct_mov_ave.value = 1 - v.correct_mov_ave.value
        elif v.correct_mov_ave.value > v.threshold: #Threshold crossed on this trial.
            v.threshold_crossed=True
            v.trials_till_reversal = randint(v.trials_post_threshold[0],v.trials_post_threshold[1])

# State independent behaviour.

def all_states(event):
    # When 'session_timer' event occurs stop framework to end session.
    if event == 'session_timer':
        stop_framework()