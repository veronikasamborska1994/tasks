# A script for testing the hardware, optionally run by the cli.run_experiment() before running the experiment
# so the user can check the hardware is all working as expected.

from pyControl.utility import *
import hardware_definition as hw

# States and events.

states = ['init_state_poke_i',
          'check_solenoid_A',
          'check_solenoid_B']

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
          'poke_6_out']

v.poke_map = {'poke_i': 1, # Trial initiation poke number.
              'poke_a': 5, # Choice poke A poke number
              'poke_b': 3} 

v.duration_reward=200*ms

initial_state = 'init_state_poke_i'

# Run start and stop behaviour.

def run_start():  # 
    hw.houselight.on()
    poke_dict = {1: hw.poke_1,
                 2: hw.poke_2,
                 3: hw.poke_3,
                 4: hw.poke_4,
                 5: hw.poke_5,
                 6: hw.poke_6} 
    hw.poke_i = poke_dict[v.poke_map['poke_i']]
    hw.poke_a = poke_dict[v.poke_map['poke_a']]
    hw.poke_b = poke_dict[v.poke_map['poke_b']]
    #hw.poke_a.SOL = hw.SOL_B
    #hw.poke_b.SOL = hw.SOL_A

def run_end():  
    hw.off()

# State & event dependent behaviour.

def init_state_poke_i(event):
    # Select left or right poke.
    if event == 'entry':
        hw.poke_i.LED.on()
    elif event == hw.poke_i.input.rising_event:
        goto_state('check_solenoid_A')
    elif event == 'exit':
        hw.poke_i.LED.off()

def check_solenoid_A(event):
    if event == 'entry':
        hw.poke_a.LED.on()
    elif event==hw.poke_i.input.rising_event:
        hw.poke_a.SOL.on()
        hw.speaker.noise()
    elif event==hw.poke_i.input.falling_event:
        hw.poke_a.SOL.off()
        hw.speaker.off()
    elif event == hw.poke_b.input.rising_event:
        goto_state('check_solenoid_B')
    elif event == 'exit':
        hw.poke_a.LED.off()

def check_solenoid_B(event):
    if event == 'entry':
        hw.poke_b.LED.on()
    elif event==hw.poke_i.input.rising_event:
        hw.poke_b.SOL.on()
        hw.speaker.sine(5000)
    elif event==hw.poke_i.input.falling_event:
        hw.poke_b.SOL.off()
        hw.speaker.off()
    elif event == hw.poke_a.input.rising_event:
        goto_state('check_solenoid_A')
    elif event == 'exit':
        hw.poke_b.LED.off()

