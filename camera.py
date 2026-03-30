from settings import *
from frustum import Frustum


class Camera:
    def __init__(self, position, yaw, pitch):
        self.position = glm.vec3(position)
        self.yaw = glm.radians(yaw)
        self.pitch = glm.radians(pitch)

        self.up = glm.vec3(0, 1, 0)
        self.right = glm.vec3(1, 0, 0)
        self.forward = glm.vec3(0, 0, -1)

        self.m_proj = glm.perspective(V_FOV, ASPECT_RATIO, NEAR, FAR)
        self.m_view = glm.mat4()

        self.frustum = Frustum(self)

    def update(self):
        self.update_vectors()
        self.update_view_matrix()

    def update_view_matrix(self):
        self.m_view = glm.lookAt(self.position, self.position + self.forward, self.up)

    def update_vectors(self):
        self.forward.x = glm.cos(self.yaw) * glm.cos(self.pitch)
        self.forward.y = glm.sin(self.pitch)
        self.forward.z = glm.sin(self.yaw) * glm.cos(self.pitch)

        self.forward = glm.normalize(self.forward)
        self.right = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.right, self.forward))

    def rotate_pitch(self, delta_y):
        self.pitch -= delta_y
        self.pitch = glm.clamp(self.pitch, -PITCH_MAX, PITCH_MAX)

    def rotate_yaw(self, delta_x):
        self.yaw += delta_x

    def move_left(self, velocity):
        # horizontal-only movement (XZ plane)
        right_xz = glm.normalize(glm.vec3(self.right.x, 0, self.right.z))
        self.position -= right_xz * velocity

    def move_right(self, velocity):
        # horizontal-only movement (XZ plane)
        right_xz = glm.normalize(glm.vec3(self.right.x, 0, self.right.z))
        self.position += right_xz * velocity

    def move_up(self, velocity):
        # move along world Y axis, not camera-relative up
        self.position.y += velocity

    def move_down(self, velocity):
        # move along world Y axis, not camera-relative up
        self.position.y -= velocity

    def move_forward(self, velocity):
        # horizontal-only movement (XZ plane)
        forward_xz = glm.normalize(glm.vec3(self.forward.x, 0, self.forward.z))
        self.position += forward_xz * velocity

    def move_back(self, velocity):
        # horizontal-only movement (XZ plane)
        forward_xz = glm.normalize(glm.vec3(self.forward.x, 0, self.forward.z))
        self.position -= forward_xz * velocity