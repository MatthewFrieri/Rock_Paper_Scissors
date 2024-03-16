#https://www.vobarian.com/collisions/2dcollisions2.pdf

import pygame as pg
from random import randint, choice
from math import dist, sqrt
import itertools
import sys


pg.init()

WIDTH, HEIGHT = 800, 800

# Setup
WIN = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Rock Paper Scissors")
FPS = 120

def dotProduct(v1, v2):
    return v1[0]*v2[0] + v1[1]*v2[1]


class Box():
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h


class Particle():
    particles = []
    wallCollisionFriction = 0.8
    particleCollisionFriction = 1
    surfaceFriction = 1


    def __init__(self, m, pos, vel, rad):
        Particle.particles.append(self)
        self.rock = pg.transform.scale(pg.image.load("Sprites\\rock.png").convert_alpha(), (rad*2, rad*2))
        self.paper = pg.transform.scale(pg.image.load("Sprites\\paper.png").convert_alpha(), (rad*2, rad*2))
        self.scissors = pg.transform.scale(pg.image.load("Sprites\\scissors.png").convert_alpha(), (rad*2, rad*2))

        self.m = m
        self.pos = pos
        self.vel = vel
        self.acc = [0, 0]
        self.rad = rad
        self.state = choice(["r", "p", "s"])
        

    def draw(self):
        if self.state == "r":
            WIN.blit(self.rock, (self.pos[0]-self.rad, self.pos[1]-self.rad))
        if self.state == "p":
            WIN.blit(self.paper, (self.pos[0]-self.rad, self.pos[1]-self.rad))
        if self.state == "s":
            WIN.blit(self.scissors, (self.pos[0]-self.rad, self.pos[1]-self.rad))


    def update(self, dt):
        self.pos[0] += self.vel[0]*dt
        self.pos[1] += self.vel[1]*dt

        self.vel[0] += self.acc[0]*dt
        self.vel[1] += self.acc[1]*dt

        # Correct wall glitch
        if self.pos[0] < self.rad:
            self.pos[0] = self.rad
            
        if WIDTH-self.rad < self.pos[0]:
            self.pos[0] = WIDTH-self.rad

        if self.pos[1] < self.rad:
            self.pos[1] = self.rad

        if HEIGHT-self.rad < self.pos[1]:
            self.pos[1] = HEIGHT-self.rad

        Particle.wallCollision(self)


        self.vel[0] *= Particle.surfaceFriction
        self.vel[1] *= Particle.surfaceFriction

    def wallCollision(self):
        if (self.pos[0] - self.rad <= 0) or (self.pos[0] + self.rad >= WIDTH):
            self.vel[0] *= -Particle.wallCollisionFriction
        if (self.pos[1] - self.rad <= 0) or (self.pos[1] + self.rad >= HEIGHT):
            self.vel[1] *= -Particle.wallCollisionFriction

    def getPossibleCollisions(lst):
        combinations = []
        for L in range(len(lst) + 1):
            for subset in itertools.combinations(lst, L):
                if len(subset) == 2:
                    combinations.append(subset)
        return combinations

    def removeDuplicates(combinations):
        new = []
        for subset in combinations:
            if subset not in new:
                new.append(subset)
        return new

    def particleCollisions(grid):
        allCombinations = []
        for i, row in enumerate(grid):
            for j, active in enumerate(row):
                if len(active) > 1:

                    combinations = Particle.getPossibleCollisions(active)
        
                    for subset in combinations:
                        allCombinations.append(subset)
                    

        allCombinations = Particle.removeDuplicates(allCombinations)
    
        for subset in allCombinations:

            p1 = subset[0]
            p2 = subset[1]

            if p1 != p2 and dist(p1.pos, p2.pos) < p1.rad + p2.rad:
                
                # Update velocities              
                unitNormal, unitTangent = Particle.getUnitVectors(p1, p2)
                p1NormalPrimeS, p1TangentPrimeS, p2NormalPrimeS, p2TangentPrimeS = Particle.getScalarVelocities(p1, p2, unitNormal, unitTangent)
                p1NormalPrime, p1TangentPrime, p2NormalPrime, p2TangentPrime = Particle.convertScalarsToVectors(unitNormal, unitTangent, p1NormalPrimeS, p1TangentPrimeS, p2NormalPrimeS, p2TangentPrimeS)
                p1Prime, p2Prime = Particle.getFinalVelocities(p1NormalPrime, p1TangentPrime, p2NormalPrime, p2TangentPrime)

                p1.vel = [p1Prime[0] * Particle.particleCollisionFriction, p1Prime[1] * Particle.particleCollisionFriction]
                p2.vel = [p2Prime[0] * Particle.particleCollisionFriction, p2Prime[1] * Particle.particleCollisionFriction]
                    
                states = [p1.state, p2.state]
                if "r" in states and "p" in states:
                    p1.state = "p"
                    p2.state = "p"
                elif "r" in states and "s" in states:
                    p1.state = "r"
                    p2.state = "r"
                elif "p" in states and "s" in states:
                    p1.state = "s"
                    p2.state = "s"


    def getUnitVectors(p1, p2):
        normal = [p2.pos[0] - p1.pos[0], p2.pos[1] - p1.pos[1]]
        absNormal = sqrt(normal[0]**2 + normal[1]**2)
        unitNormal = [normal[0]/absNormal, normal[1]/absNormal]

        unitTangent = [-unitNormal[1], unitNormal[0]]

        return unitNormal, unitTangent


    def getScalarVelocities(p1, p2, unitNormal, unitTangent):
        # Before the collision
        p1NormalS = dotProduct(unitNormal, p1.vel)
        p1TangentS = dotProduct(unitTangent, p1.vel)
       
        p2NormalS = dotProduct(unitNormal, p2.vel)
        p2TangentS = dotProduct(unitTangent, p2.vel)
        
        # After the collision
        p1TangentPrimeS = p1TangentS
        p2TangentPrimeS = p2TangentS

        p1NormalPrimeS = (p1NormalS*(p1.m - p2.m) + 2*p2.m*p2NormalS) / (p1.m + p2.m)
        p2NormalPrimeS = (p2NormalS*(p2.m - p1.m) + 2*p1.m*p1NormalS) / (p1.m + p2.m)

        return p1NormalPrimeS, p1TangentPrimeS, p2NormalPrimeS, p2TangentPrimeS 

    def convertScalarsToVectors(unitNormal, unitTangent, p1NormalPrimeS, p1TangentPrimeS, p2NormalPrimeS, p2TangentPrimeS):
        p1NormalPrime = [unitNormal[0] * p1NormalPrimeS, unitNormal[1] * p1NormalPrimeS]
        p1TangentPrime = [unitTangent[0] * p1TangentPrimeS, unitTangent[1] * p1TangentPrimeS]

        p2NormalPrime = [unitNormal[0] * p2NormalPrimeS, unitNormal[1] * p2NormalPrimeS]
        p2TangentPrime = [unitTangent[0] * p2TangentPrimeS, unitTangent[1] * p2TangentPrimeS]

        return p1NormalPrime, p1TangentPrime, p2NormalPrime, p2TangentPrime

    def getFinalVelocities(p1NormalPrime, p1TangentPrime, p2NormalPrime, p2TangentPrime):
        p1Prime = [p1NormalPrime[0] + p1TangentPrime[0], p1NormalPrime[1] + p1TangentPrime[1]]
        p2Prime = [p2NormalPrime[0] + p2TangentPrime[0], p2NormalPrime[1] + p2TangentPrime[1]]

        return p1Prime, p2Prime   

    def generateParticles(smart, n, rad, vel, offset):
        particles = []

        if smart:
            x = rad*(2-offset)*1.5
            y = rad*(2-offset)*1.5
            for _ in range(n):
                newRad = randint(int(rad*offset), int(rad*(2-offset)))
                mass = newRad * 100
                particles.append(Particle(mass, [x, y], [randint(-vel, vel), randint(-vel, vel)], newRad))
                x += rad*3
                if x >= WIDTH-rad*1.5:
                    x = rad*1.5
                    y += rad*3

        else:
            for _ in range(n):
                newRad = randint(int(rad*offset), int(rad*(2-offset)))
                mass = newRad * 100
                particles.append(Particle(mass, [randint(rad, WIDTH-rad), randint(rad, HEIGHT-rad)], [randint(-vel, vel), randint(-vel, vel)], newRad))

        return particles

    def generateGrid(n):
        grid = []
        for i in range(n):
            row = []
            for j in range(n):
                row.append([])
            grid.append(row)
        return grid

    def fillGrid(grid):
        width = WIDTH/len(grid[0])
        height = HEIGHT/len(grid)

        for i, row in enumerate(grid):
            for j, active in enumerate(row):

                b = Box(i*width, j*height, width, height)
                
                for p in Particle.particles:
                    if Particle.particleTouchingBox(p, b):
                        active.append(p)
        return grid

    def pointInBox(pt, b):
        if b.x <= pt[0] <= b.x+b.w and b.y <= pt[1] <= b.y+b.h:
            return True
        else:
            return False

    def particleTouchingBox(p, b):
        B = Box(b.x-p.rad, b.y-p.rad, b.w+2*p.rad, b.h+2*p.rad)

        if not Particle.pointInBox(p.pos, B):
            return False

        cornerBoxes = []
        cornerBoxes.append((Box(B.x, B.y, p.rad, p.rad), (b.x, b.y)))
        cornerBoxes.append((Box(b.x+b.w, B.y, p.rad, p.rad), (b.x+b.w, b.y)))
        cornerBoxes.append((Box(B.x, b.y+b.h, p.rad, p.rad), (b.x, b.y+b.h)))
        cornerBoxes.append((Box(b.x+b.w, b.y+b.h, p.rad, p.rad), (b.x+b.w, b.y+b.h)))

        for corner in cornerBoxes:

            if Particle.pointInBox(p.pos, corner[0]):
                if dist(p.pos, corner[1]) <= p.rad:
                    return True
                else:
                    return False

        return True 

def main():
    clock = pg.time.Clock()

    particles = []
    particles = Particle.generateParticles(True, 70, 20, 400, 0.5)


    # Main loop
    while True:
        clock.tick(FPS)

        # Events
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()

        dt = 1/FPS


        WIN.fill("black")

        grid = Particle.generateGrid(8)
        
        grid = Particle.fillGrid(grid)
        Particle.particleCollisions(grid)

        for p in particles:
            p.update(dt)
        for p in particles:
            p.draw()


        pg.display.update()        

main()
