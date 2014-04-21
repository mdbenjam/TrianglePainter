class Stroke:
    def __init__(self):
        self.mouse = []
        self.window = None
        
        self.color = None
        self.hardness = None
        self.size = None
        self.numSides = None

    def load(self, f):
        line = f.readLine()
        while line != '#':
            
            line = f.readLine()

        # num_quads = int(f.readline())
        # color = f.readline().split(',')
        # self.color = [float(color[0]), float(color[1]), float(color[2]), float(color[3])]
        # for i in range(num_quads):
        #     q = []
        #     for j in range(4):
        #         line = f.readline()
        #         s = line.split(',')
        #         q.append([float(s[0]), float(s[1])])
        #     self.quads.append(q)

        # num_quads = int(f.readline())
        # color = f.readline().split(',')
        # self.fallOffColor = [float(color[0]), float(color[1]), float(color[2]), float(color[3])]
        # for i in range(num_quads):
        #     q = []
        #     for j in range(4):
        #         line = f.readline()
        #         s = line.split(',')
        #         q.append([float(s[0]), float(s[1])])
        #     self.fallOffQuads.append(q)
