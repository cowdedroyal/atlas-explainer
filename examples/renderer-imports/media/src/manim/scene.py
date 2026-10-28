from manim import Scene, Dot, Square, RIGHT, LEFT

class Flow(Scene):
    def construct(self):
        dot = Dot(LEFT, color="#6aa9cf")
        self.add(Square(side_length=1.5, color="#98a2b3"), dot)
        self.play(dot.animate.shift(2 * RIGHT), run_time=1)
