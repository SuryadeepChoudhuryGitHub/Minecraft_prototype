#version 330 core

layout (location = 0) out vec4 fragColor;

in vec3 marker_color;
in vec2 uv;

uniform sampler2D u_texture_0;

void main() {
    fragColor = texture(u_texture_0, uv);
    // darken: subtract marker_color so the outline goes black
    fragColor.rgb -= marker_color;
    // show only the dark border pixels; discard bright (transparent) ones
    fragColor.a = (fragColor.r + fragColor.b > 1.5) ? 0.0 : 1.0;
}