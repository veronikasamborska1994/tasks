
from pyControl.utility import *
import hardware_definition as hw

#-------------------------------------------------------------------------
# States and events.
#-------------------------------------------------------------------------

states = ['reward_not_available',
          'reward_available',
          'instrumental_reward']

events = ['poke_1',
          'poke_2',
          'poke_1_out',
          'poke_2_out',
          'session_timer',
          'transition_timer_pavlovian',
          'transition_timer_instrumental',
          'pavlovian_reward', 'pavolvian_off_timer','pav_reward','pavlovian_state','block_timer']

initial_state = 'reward_not_available'

#-------------------------------------------------------------------------
# Variables and Parameters
#-------------------------------------------------------------------------

# Parameters
v.session_duration = 30*second
v.reward_durations = [100,100] # Reward delivery duration (ms) [a, b]
v.ITI_duration = 1.25*second # Inter trial interval duration.
v.minumum_waiting_period = 1*second # Minimum waiting period till a pavlovian cue
# Variable
v.n_rewards_pavlovian = 0 # Number of pavlovian rewards delivered.
v.n_rewards_instrumental = 0 # Number of instrumental rewards obtained.
v.till_reward_time_ins = 5*second # Mean rate for instrumental reward to become available
v.till_reward_time_pv = 2*second # Mean rate for pavlovian cue 
v.block_duration = 10*second # Duration of ech block 
v.current_block=0 # Block number
v.inter_reward_interval= [3, 5, 10, 15] # List of mean instrumental reward rates 

#-------------------------------------------------------------------------        
# Define behaviour.
#-------------------------------------------------------------------------

# Run start and stop behaviour.

def run_start():
     hw.poke_a = hw.poke_1
     hw.poke_b = hw.poke_2
     set_timer('session_timer', v.session_duration)  
     set_timer('transition_timer_pavlovian', v.minumum_waiting_period + exp_rand(v.till_reward_time_pv))
     set_timer('block_timer',v.block_duration)
def run_end():
    # Turn off all hardware outputs.  
    hw.off()

# State behaviour functions

def reward_not_available(event):
     if event == 'entry':
          set_timer('transition_timer_instrumental', exp_rand(v.till_reward_time_ins))
     elif event == 'transition_timer_instrumental':
          goto_state('reward_available')

def reward_available(event):
     if event == hw.poke_b.input.rising_event:
          goto_state('instrumental_reward')

def  instrumental_reward(event):
     if event == 'entry':
          hw.poke_b.SOL.on()
          timed_goto_state('reward_not_available', v.reward_durations[0])
          v.n_rewards_instrumental += 1
     elif event == 'exit':
          hw.poke_b.SOL.off()
          print('RP#:{}, RI#:{}, B#:{}]'.format(v.n_rewards_pavlovian, v.n_rewards_instrumental,v.current_block))


# State independent behaviour.
def all_states(event):
     if event == 'block_timer':
          v.current_block +=1
          v.till_reward_time_inst =v.inter_reward_interval[v.current_block%len(v.inter_reward_interval)]
          set_timer('block_timer',v.block_duration)
     if event == 'transition_timer_pavlovian':
          publish_event('pavlovian_state')
          hw.poke_a.LED.on()
          hw.speaker.clicks(5)
          set_timer('pavlovian_reward', 10*second)
     elif event == 'pavlovian_reward':
          hw.speaker.off()
          hw.poke_a.LED.off()
          publish_event('pav_reward')
          hw.poke_a.SOL.on()
          v.n_rewards_pavlovian += 1
          set_timer('pavolvian_off_timer', v.reward_durations[0])
     elif event == 'pavolvian_off_timer': 
          hw.poke_a.SOL.off()
          set_timer('transition_timer_pavlovian', v.minumum_waiting_period + exp_rand(v.till_reward_time_pv))
     elif event == 'session_timer':
          stop_framework()
