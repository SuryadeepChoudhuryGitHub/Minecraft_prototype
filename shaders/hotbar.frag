#version 330 core

in vec2 uv;
out vec4 fragColor;

uniform sampler2D u_texture;

void main() {
    vec4 color = texture(u_texture, uv);
    if (color.a < 0.01) discard;
    fragColor = color;
}
