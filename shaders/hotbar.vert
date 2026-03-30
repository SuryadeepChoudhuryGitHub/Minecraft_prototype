#version 330 core

in vec2 in_position;
in vec2 in_texcoord;

out vec2 uv;

void main() {
    uv = in_texcoord;
    gl_Position = vec4(in_position, 0.0, 1.0);
}
