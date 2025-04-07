#!usr/bin/env python

'''

This script produces a 480p resolution mp4 video file. 
Please modify as required for desired output.

@author: Nick + MS Copilot
@run: manim -pql intro-card.py MultimodalIVRIntro
@destination: ./media/videos/intro-card/480p15/partial_movie_files/MultimodalIVRIntro.mp4
@requirements: pip install manim
'''

from manim import *

class MultimodalIVRIntro(Scene):
    def construct(self):
        # Create the background rectangle with gradient colors
        background = Rectangle(width=14, height=8)
        background.set_fill(color=[BLUE_E, PURPLE_E], opacity=1)
        background.set_stroke(width=0)
        self.add(background)

        # Create the title text
        title = Text("Multimodal IVR", font_size=72, gradient=(YELLOW, GOLD))

        # Add subtitle for emphasis
        subtitle = Text("Interactive Voice Response System", font_size=36).set_color(GRAY_A)
        subtitle.next_to(title, DOWN)

        # Create a glowing circle behind the text
        glow = Circle(radius=4, color=WHITE).set_fill(WHITE, opacity=0.2)
        glow.move_to(title.get_center())

        # Animation Sequence
        self.play(FadeIn(background))  # Fade in the background
        self.wait(0.5)
        self.play(FadeIn(glow, scale=0.5))  # Glowing effect
        self.play(FadeIn(title), run_time=2)  # Bring in the title text smoothly
        self.wait(0.5)
        self.play(FadeIn(subtitle, shift=UP), run_time=1)  # Fade in subtitle
        self.wait(1)
        self.play(
            Indicate(title, scale_factor=1.1, color=GOLD),  # Highlight the title
            Flash(glow, color=WHITE, line_length=0.5, num_lines=16)  # Glowing flash
        )
        self.wait(2)

        # Outro animation
        self.play(
            FadeOut(title, shift=UP),
            FadeOut(subtitle, shift=DOWN),
            FadeOut(glow),
            FadeOut(background, scale=2)
        )

if(__name__=='__main__'):
    print("Hello World! Please use the manim command to run this file, V.")