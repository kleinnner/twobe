#!/usr/bin/env python3
"""
TwoBe by Adobo - A free, open-source 3D model viewer
Copyright (c) 2025 Adobo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import os
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import pywavefront

# Initialize Pygame and OpenGL
pygame.init()
width, height = 800, 600
pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
pygame.display.set_caption("TwoBe by Adobo - 3D Model Viewer")

# Set up OpenGL
glEnable(GL_DEPTH_TEST)
glClearColor(0.1, 0.1, 0.1, 1.0)  # Dark background for better visibility

# Camera control variables
rotate_x, rotate_y = 0.0, 0.0
zoom_level = 1.0
dragging = False
last_pos = (0, 0)
camera_distance = -5.0  # Dynamic initial distance

# Default cube model (used if no file is loaded)
default_vertices = [
    (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1),
    (1, -1, 1), (1, 1, 1), (-1, -1, 1), (-1, 1, 1)
]
default_faces = [
    (0, 1, 2), (0, 2, 3), (4, 5, 6), (4, 6, 7),
    (0, 4, 7), (0, 7, 3), (1, 5, 6), (1, 6, 2),
    (0, 1, 5), (0, 5, 4), (2, 3, 7), (2, 7, 6)
]
default_lines = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
                 (0, 4), (1, 5), (2, 6), (3, 7)]
vertices = default_vertices
faces = default_faces
lines = default_lines

# Camera icon
camera_icon_rect = pygame.Rect(width - 60, height - 60, 50, 50)

def normalize_model(vertices):
    """Normalize and center the model to fit within the view."""
    if not vertices:
        return vertices, 1.0
    
    # Compute bounding box
    min_x = min(v[0] for v in vertices)
    max_x = max(v[0] for v in vertices)
    min_y = min(v[1] for v in vertices)
    max_y = max(v[1] for v in vertices)
    min_z = min(v[2] for v in vertices)
    max_z = max(v[2] for v in vertices)

    # Center the model
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    center_z = (min_z + max_z) / 2
    centered_vertices = [(v[0] - center_x, v[1] - center_y, v[2] - center_z) for v in vertices]

    # Compute scale factor
    extent = max(max_x - min_x, max_y - min_y, max_z - min_z)
    scale = 2.0 / extent if extent > 0 else 1.0  # Fit within a 2-unit box

    # Apply scale
    normalized_vertices = [(v[0] * scale, v[1] * scale, v[2] * scale) for v in centered_vertices]

    # Return normalized vertices and a camera distance based on extent
    return normalized_vertices, max(5.0, extent * 1.5)

def parse_obj_lines(file_path):
    """Manually parse 'l' statements from the OBJ file."""
    lines = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('l'):
                parts = line.strip().split()
                if len(parts) > 2:
                    vertex_indices = [int(idx) - 1 for idx in parts[1:]]
                    for i in range(len(vertex_indices) - 1):
                        lines.append((vertex_indices[i], vertex_indices[i + 1]))
    return lines

def load_model():
    """Load a 3D model file and normalize it."""
    global vertices, faces, lines, camera_distance
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Open 3D Model",
        filetypes=[("OBJ files", "*.obj"), ("All files", "*.*")]
    )
    if file_path:
        try:
            model = pywavefront.Wavefront(file_path, collect_faces=True)
            vertices = model.vertices
            faces = model.mesh_list[0].faces if model.mesh_list else []
            lines = parse_obj_lines(file_path)
            vertices, camera_distance = normalize_model(vertices)  # Normalize and set camera distance
            print(f"Loaded model from {file_path}")
            print(f"Vertices: {len(vertices)}, Faces: {len(faces)}, Lines: {len(lines)}")
            print(f"Camera distance set to: {camera_distance}")
        except Exception as e:
            print(f"Failed to load model: {e}")
            vertices, faces, lines = default_vertices, default_faces, default_lines
            camera_distance = -5.0
    else:
        vertices, faces, lines = default_vertices, default_faces, default_lines
        camera_distance = -5.0

def draw_model():
    """Draw the loaded 3D model (faces and lines)."""
    glColor3f(1.0, 1.0, 1.0)  # White color for visibility
    # Draw faces
    glBegin(GL_TRIANGLES)
    for face in faces:
        for vertex_idx in face:
            glVertex3fv(vertices[vertex_idx])
    glEnd()

    # Draw lines
    glBegin(GL_LINES)
    for line in lines:
        for vertex_idx in line:
            glVertex3fv(vertices[vertex_idx])
    glEnd()

def draw_camera_icon():
    """Draw a simple camera icon."""
    pygame.draw.rect(pygame.display.get_surface(), (255, 255, 255), camera_icon_rect)
    pygame.draw.rect(pygame.display.get_surface(), (0, 0, 0), camera_icon_rect, 2)

def save_screenshot():
    """Save a screenshot to Documents/TwoBe."""
    save_dir = os.path.join(os.path.expanduser("~"), "Documents", "TwoBe")
    os.makedirs(save_dir, exist_ok=True)

    glPixelStorei(GL_PACK_ALIGNMENT, 1)
    data = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
    surface = pygame.image.fromstring(data, (width, height), "RGB", True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(save_dir, f"twobe_screenshot_{timestamp}.png")
    pygame.image.save(surface, filename)
    print(f"Screenshot saved to {filename}")

def main():
    global rotate_x, rotate_y, zoom_level, dragging, last_pos, camera_distance

    clock = pygame.time.Clock()
    running = True

    # Prompt to load a model at startup
    load_model()

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if camera_icon_rect.collidepoint(event.pos):
                        save_screenshot()
                    else:
                        dragging = True
                        last_pos = event.pos
                elif event.button == 4:  # Scroll up to zoom in
                    zoom_level = max(0.1, zoom_level - 0.1)
                elif event.button == 5:  # Scroll down to zoom out
                    zoom_level = min(5.0, zoom_level + 0.1)
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False
            elif event.type == MOUSEMOTION and dragging:
                dx, dy = event.pos[0] - last_pos[0], event.pos[1] - last_pos[1]
                rotate_x += dy * 0.5
                rotate_y += dx * 0.5
                last_pos = event.pos
            elif event.type == KEYDOWN:
                if event.key == K_o:  # Press 'O' to open a new file
                    load_model()

        # Clear the screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Apply camera transformations
        gluPerspective(45, (width / height), 0.1, 100.0)  # Increased far plane
        glTranslatef(0.0, 0.0, camera_distance * zoom_level)
        glRotatef(rotate_x, 1, 0, 0)
        glRotatef(rotate_y, 0, 1, 0)

        # Draw the model
        draw_model()

        # Switch to 2D mode to draw the camera icon
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        pygame.display.flip()  # Update screen before drawing 2D
        draw_camera_icon()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        # Update display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    print("Starting TwoBe by Adobo")
    print("Controls: Left-click drag to rotate, Scroll to zoom, Click camera icon to screenshot, 'O' to open file")
    main()