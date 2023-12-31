import numpy as np
from flight_controller import FlightController
from drone import Drone
from typing import Tuple
import pygame
import pickle
from main import *
import os, datetime
import pandas as pd

class CustomController(FlightController):


    def __init__(self):
        """Creates a heuristic flight controller with some specified parameters

        """
        pass
        

    def get_max_simulation_steps(self):
            return 3000 # You can alter the amount of steps you want your program to run for here


    def get_thrusts(self, drone: Drone) -> Tuple[float, float]:
        """Takes a given drone object, containing information about its current state
        and calculates a pair of thrust values for the left and right propellers.

        Args:
            drone (Drone): The drone object containing the information about the drones state.

        Returns:
            Tuple[float, float]: A pair of floating point values which respectively represent the thrust of the left and right propellers, must be between 0 and 1 inclusive.
        """

        target_point = drone.get_next_target()
        
        dx = target_point[0] - drone.x
        dy = target_point[1] - drone.y
        
        self.dist_from_last_step = np.sqrt(dx ** 2 + dy ** 2 )

        thrust_adj = np.clip(dy * self.ky, -self.abs_thrust_delta, self.abs_thrust_delta)
        target_pitch = np.clip(dx * self.kx, -self.abs_pitch_delta, self.abs_pitch_delta)
        delta_pitch = target_pitch-drone.pitch

        thrust_left = np.clip(0.5 + thrust_adj + delta_pitch, 0.0, 1.0)
        thrust_right = np.clip(0.5 + thrust_adj - delta_pitch, 0.0, 1.0)

        # The default controller sets each propeller to a value of 0.5 0.5 to stay stationary.
        return (thrust_left, thrust_right)

    def train(self, save_path):
        """A self contained method designed to train parameters created in the initialiser.
        """
        
        
        epochs = 50
        alpha = 1e-3
        b1 = 0.9
        b2 = 0.999
        params = [1.0, 0.5, 0.1, 0.3]                
        grads = [0, 0, 0, 0]
        m = [0, 0, 0, 0]
        v = [0, 0, 0, 0]

        for n in range(epochs):
            
            ## Forward pass
            print(f"Epoch:{n+1}")
            if n==0 or (n+1) % 20 == 0:
                R1 = self.simaulation(params, n, save_path)
            else:
                R1 = self.getReturn(params)
            #print(f"Reward: {R1}")
                        
            ## Estimate grads / for backprop
            #print(f"Back prop for epoch:{n+1}")
                        
            for i in range(len(params)):
                #print(f" -- Finding Grad for parameter {i+1}")
                delta = 0.0001
                p1 = params[i]
                p2 = p1 + delta
                params_changed = params.copy()
                params_changed[i] = p2
                
                
                R2 = self.getReturn(params_changed)
                #Calclate the gradient
                dR = (R2-R1)/(p2-p1)
                grads[i] = dR
                #print(f"   - Reward is: {R2} Grad is: {dR}")
                
            ## Log the data before updating to new data
            data = {'epoch':n+1, 'params':params, 'grads':grads, 'reward': R1}            
            self.logWeights(n+1, data, save_path)
            print(f" --params {params}, Reward: {R1}, Grads: {grads}")
            #print("\n\n") 
            
            ## Update parameters
            for i in range(len(params)):
                m[i] = b1 * m[i] + (1-b1) * grads[i]
                v[i] = b2 * v[i] + (1-b2) * grads[i] ** 2
                mt_cap = m[i]/(1-b1)
                vt_cap = v[i]/(1-b2)
                params[i] = params[i] + alpha * mt_cap/(np.sqrt(vt_cap)+1e-8)          
          
    def getReturn(self, params):
        
        return_ = 0
        
        
        ## Set to new parameters
        
        self.ky = params[0]
        self.kx = params[1]
        self.abs_pitch_delta = params[2]
        self.abs_thrust_delta = params[3]
        
        # create a new drone simulation
        drone = self.init_drone()
        # 3) run simulation
        for t in range(self.get_max_simulation_steps()):
            drone.set_thrust(self.get_thrusts(drone))
            drone.step_simulation(self.get_time_interval())
            
            # Calculate return 
            return_ += self.getReward(drone)  
                
        return return_
        
    def simaulation(self, params, epoch, save_path):
        
        self.ky = params[0]
        self.kx = params[1]
        self.abs_pitch_delta = params[2]
        self.abs_thrust_delta = params[3]
        
        return_ = 0
        time_rewards = []
        
        
        # Initialise pygame
        pygame.init()
        clock = pygame.time.Clock()

        # Load the relevant graphics into pygame
        drone_img = pygame.image.load('graphics/drone_small.png')
        background_img = pygame.image.load('graphics/background.png')
        target_img = pygame.image.load('graphics/target.png')
    

        # Create the screen
        SCREEN_WIDTH = 720
        SCREEN_HEIGHT = 480
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))    
        delta_time = self.get_time_interval()           
           
            
        # create a new drone simulation
        drone = self.init_drone()
        # 3) run simulation
        for t in range(self.get_max_simulation_steps()):
            drone.set_thrust(self.get_thrusts(drone))
            drone.step_simulation(self.get_time_interval())
            # Refresh the background
            screen.blit(background_img, (0,0))
            # Draw the current drone on the screen
            draw_drone(screen, drone, drone_img)
            # Draw the next target on the screen
            draw_target(drone.get_next_target(), screen, target_img)
        
            # Actually displays the final frame on the screen
            pygame.display.flip()
        
            # Makes sure that the simulation runs at a target 60FPS
            clock.tick(60)
                
            # Calculate return 
            return_ += self.getReward(drone)
            
            ## Log return for timestep 
            
            time_rewards.append((epoch,t,return_))
            
        df = pd.DataFrame(time_rewards, columns=['epoch', 'time_step', 'reward'])        
        file_name = 'rewards_timesteps{}.csv'.format(epoch)
        file_path = os.path.join(save_path, file_name)
        df.to_csv(file_path,index=False) 
            
            
        return return_

    """
    Load the parameters of this flight controller from disk.
        """

    def getReward(self, drone : Drone):
        
         if drone.has_reached_target_last_update:
             return 50
         else:
             return -1
        
    def logWeights(self, epoch, data, save_path):
        file_name = 'params_epoch{}.pkl'.format(epoch)
        file_path = os.path.join(save_path, file_name)        
        with open(file_path,'wb') as file:
            pickle.dump(data, file)
        
    def findDistance(self, drone: Drone):
        target_point = drone.get_next_target()
        
        dx = target_point[0] - drone.x
        dy = target_point[1] - drone.y
        
        return np.sqrt(dx ** 2 + dy ** 2 )

    def load(self):
        """Load the parameters of this flight controller from disk.
        """
        try:
            parameter_array = np.load('heuristic_controller_parameters.npy')
            self.ky = parameter_array[0]
            self.kx = parameter_array[1]
            self.abs_pitch_delta = parameter_array[2]
            self.abs_thrust_delta = parameter_array[3]
        except:
            print("Could not load parameters, sticking with default parameters.")

    def save(self):
        """Save the parameters of this flight controller to disk.
        """
        parameter_array = np.array([self.ky, self.kx, self.abs_pitch_delta, self.abs_thrust_delta])
        np.save('heuristic_controller_parameters.npy', parameter_array)
        
        
if __name__ == "__main__":
    
    controller = CustomController()
    
    ## Making directory to log the training data
    newdir = os.path.join(os.getcwd(),"weights","run_"+datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    os.makedirs(newdir)
    
    ## Update read me text
    readme_text = """ Reward function with 50 for reaching the target and  -1  at each 
    time step, 3000 simulations      """
    with open(newdir+'/readme.txt', 'w') as f:
        f.write(readme_text)
        
    controller.train(newdir)