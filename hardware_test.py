# A script for testing the hardware, optionally run by the cli.run_experiment() before running the experiment
# so the user can check the hardware is all working as expected.

from pyControl.utility import *
import hardware_definition as hw

# States and events.

states = ['init_state_poke_i',
          'poke_a',
          'poke_b']

vents = [ 'poke_1',
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

v.duration_reward=200ms

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
    hw.poke_a.SOL = hw.SOL_B
    hw.poke_b.SOL = hw.SOL_A

def run_end():  
    hw.off()

# State & event dependent behaviour.

def init_state_poke_i(event):
    # Select left or right poke.
    if event == hw.poke_i.input.rising_event:
        hw.poke_i.LED.on()
        timed_gotostate('check_solenoid_A', 50*ms)
    elif event == 'exit':
        hw.poke_i.LED.off()

def check_solenoid_A(event):
    if event==poke_a.input.rising_event:
        hw.poke_a.SOl.on()
        hw.sound.noise()
        timed_gotostate('check_solenoid_B', v.duration_reward)
    elif event==poke_i.input.falling_event:
        hw.poke_a.SOl.off()
        hw.speaker.off()

def check_solenoid_B(event):
    if event==poke_b.input.rising_event:
        hw.poke_b.SOl.on()
        hw.speaker.sine(5000)
    elif event=poke_b.input.falling_event:
        hw.poke_b.Sol.off()
        hw.speaker.off()


