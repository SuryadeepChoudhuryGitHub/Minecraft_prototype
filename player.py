import pygame as pg
from camera import Camera
from settings import *
import math

# Small inward shrink on the AABB to prevent floating-point boundary errors.
COLLISION_SKIN = 0.02


class Player(Camera):
    def __init__(self, app, position=PLAYER_POS, yaw=-90, pitch=0):
        self.app = app
        self.player_speed = PLAYER_SPEED
        super().__init__(position, yaw, pitch)

        # horizontal movement (scalar speed + direction)
        self.move_speed = 0.0     # current horizontal speed (voxels/ms)
        self.move_dir_x = 0.0     # last movement direction (normalised)
        self.move_dir_z = 0.0
        # vertical velocity
        self.vel_y = 0.0

        self.is_on_ground = False

        # fly mode
        self.is_flying = False
        self.last_space_press = 0

        # sneak
        self.is_sneaking = False
        self.effective_height = PLAYER_HEIGHT  # changes when sneaking
        self.camera_y_offset = 0.0            # smooth visual offset for sneak

        # hotbar
        self.selected_slot = 0  # 0-8

        # zoom
        self.current_fov = V_FOV  # lerps toward ZOOM_FOV when C is held
        self._last_sent_fov = V_FOV

    # ================================================================== #
    #  Main loop                                                           #
    # ================================================================== #
    def update(self):
        dt = min(max(self.app.delta_time, 1.0), 50.0)
        self.mouse_control()
        self._process_physics(dt)

        # smooth sneak camera offset
        lerp = min(1.0, 0.012 * dt)
        self.camera_y_offset *= (1.0 - lerp)
        if abs(self.camera_y_offset) < 0.002:
            self.camera_y_offset = 0.0

        # smooth zoom — lerp FOV toward target
        key_state = pg.key.get_pressed()
        target_fov = ZOOM_FOV if key_state[pg.K_c] else V_FOV
        self.current_fov += (target_fov - self.current_fov) * min(1.0, ZOOM_SPEED * dt)
        # rebuild projection only when FOV meaningfully changed
        if abs(self.current_fov - self._last_sent_fov) > 0.0005:
            self._last_sent_fov = self.current_fov
            self.m_proj = glm.perspective(self.current_fov, ASPECT_RATIO, NEAR, FAR)
            self.app.shader_program.update_proj(self.m_proj)

        super().update()

    def update_view_matrix(self):
        """Override: apply smooth sneak offset to visual camera only."""
        visual_pos = glm.vec3(
            self.position.x,
            self.position.y + self.camera_y_offset,
            self.position.z
        )
        self.m_view = glm.lookAt(visual_pos, visual_pos + self.forward, self.up)

    def handle_event(self, event):
        # double-tap spacebar → toggle fly / walk
        if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
            now = pg.time.get_ticks()
            if now - self.last_space_press < DOUBLE_TAP_TIME:
                self.is_flying = not self.is_flying
                self.vel_y = 0.0
            self.last_space_press = now

        # hotbar: number keys 1-9
        if event.type == pg.KEYDOWN:
            if pg.K_1 <= event.key <= pg.K_9:
                self.selected_slot = event.key - pg.K_1

        # hotbar: scroll wheel
        if event.type == pg.MOUSEWHEEL:
            self.selected_slot = (self.selected_slot - event.y) % 9

        # voxel interaction: left click = break, right click = place
        if event.type == pg.MOUSEBUTTONDOWN:
            voxel_handler = self.app.scene.world.voxel_handler
            voxel_handler.new_voxel_id = HOTBAR_BLOCKS[self.selected_slot]
            if event.button == 1:
                voxel_handler.remove_voxel()
            if event.button == 3:
                voxel_handler.add_voxel()

    def mouse_control(self):
        mouse_dx, mouse_dy = pg.mouse.get_rel()
        if mouse_dx:
            self.rotate_yaw(delta_x=mouse_dx * MOUSE_SENSITIVITY)
        if mouse_dy:
            self.rotate_pitch(delta_y=mouse_dy * MOUSE_SENSITIVITY)

    # ================================================================== #
    #  Unified physics pipeline                                            #
    # ================================================================== #
    def _process_physics(self, dt):
        key_state = pg.key.get_pressed()

        # ---- sneak state ---- #
        self._update_sneak(key_state)

        max_speed = FLY_SPEED if self.is_flying else self.player_speed
        if self.is_sneaking:
            max_speed = SNEAK_SPEED
        if key_state[pg.K_LCTRL]:
            max_speed *= 2.0

        # ---- 1. horizontal input → accelerate / decelerate ---- #
        forward_xz = glm.normalize(glm.vec3(self.forward.x, 0, self.forward.z))
        right_xz   = glm.normalize(glm.vec3(self.right.x,   0, self.right.z))

        wish_x, wish_z = 0.0, 0.0
        if key_state[pg.K_w]:
            wish_x += forward_xz.x;  wish_z += forward_xz.z
        if key_state[pg.K_s]:
            wish_x -= forward_xz.x;  wish_z -= forward_xz.z
        if key_state[pg.K_d]:
            wish_x += right_xz.x;    wish_z += right_xz.z
        if key_state[pg.K_a]:
            wish_x -= right_xz.x;    wish_z -= right_xz.z

        wish_len = math.sqrt(wish_x * wish_x + wish_z * wish_z)
        has_input = wish_len > 0.001

        if has_input:
            # direction instantly follows where you're facing
            self.move_dir_x = wish_x / wish_len
            self.move_dir_z = wish_z / wish_len
            # accelerate scalar speed toward max
            step = PLAYER_ACCEL * dt
            if not self.is_flying and not self.is_on_ground:
                step *= AIR_SPEED_FACTOR
            self.move_speed = min(self.move_speed + step, max_speed)
        else:
            # decelerate speed, keep last direction
            self.move_speed = max(0.0, self.move_speed - PLAYER_DECEL * dt)

        # immediately clamp speed when airborne (not flying) —
        # prevents full ground speed carrying over for even tiny hops
        if not self.is_flying and not self.is_on_ground:
            air_cap = max_speed * AIR_SPEED_FACTOR
            if self.move_speed > air_cap:
                self.move_speed -= PLAYER_DECEL * dt  # bleed down fast
                self.move_speed = max(self.move_speed, air_cap)

        # ---- 2. vertical input ---- #
        if self.is_flying:
            fly_max = FLY_SPEED * (2.0 if key_state[pg.K_LCTRL] else 1.0)
            desired_vy = 0.0
            if key_state[pg.K_SPACE]:
                desired_vy = fly_max
            elif key_state[pg.K_LSHIFT]:
                desired_vy = -fly_max
            rate = PLAYER_ACCEL if desired_vy != 0.0 else PLAYER_DECEL
            step = rate * dt
            diff = desired_vy - self.vel_y
            if abs(diff) <= step:
                self.vel_y = desired_vy
            else:
                self.vel_y += math.copysign(step, diff)
        else:
            if key_state[pg.K_SPACE] and self.is_on_ground:
                self.vel_y = JUMP_SPEED
                self.is_on_ground = False

        # ---- 3. position update ---- #
        dx = self.move_dir_x * self.move_speed * dt
        dz = self.move_dir_z * self.move_speed * dt

        if self.is_flying:
            dy = self.vel_y * dt
            self.position.x += dx
            self.position.y += dy
            self.position.z += dz
        else:
            # horizontal with wall collision + sneak edge prevention
            self._try_move(dx, dz)

            # edge detection (walked off a ledge?)
            if self.is_on_ground:
                if not self._collides_at(self.position.x,
                                         self.position.y - 0.05,
                                         self.position.z):
                    self.is_on_ground = False

            # vertical movement only when airborne
            if not self.is_on_ground:
                dy = self.vel_y * dt
                new_y = self.position.y + dy
                if not self._collides_at(self.position.x, new_y, self.position.z):
                    self.position.y = new_y
                else:
                    if dy < 0:
                        self.is_on_ground = True
                        feet_y = self.position.y - self.effective_height
                        snapped_feet = math.floor(feet_y + dy) + 1.0
                        self.position.y = snapped_feet + self.effective_height
                    self.vel_y = 0.0

        # ---- 4. gravity only when airborne ---- #
        if not self.is_flying and not self.is_on_ground:
            self.vel_y -= GRAVITY * dt
            if self.vel_y < -TERMINAL_VELOCITY:
                self.vel_y = -TERMINAL_VELOCITY

    # ================================================================== #
    #  Sneak                                                               #
    # ================================================================== #
    def _update_sneak(self, key_state):
        """Handle crouch start / stop with height transition."""
        want_sneak = (not self.is_flying
                      and key_state[pg.K_LSHIFT]
                      and self.is_on_ground)

        height_diff = PLAYER_HEIGHT - SNEAK_EYE_HEIGHT

        if want_sneak and not self.is_sneaking:
            # start sneaking — hitbox shrinks instantly, camera glides down
            self.is_sneaking = True
            self.effective_height = SNEAK_EYE_HEIGHT
            self.position.y -= height_diff
            self.camera_y_offset += height_diff   # compensate so camera stays, then lerps

        elif not want_sneak and self.is_sneaking:
            # try to stand up — check if there's room above
            new_py = self.position.y + height_diff
            old_height = self.effective_height
            self.effective_height = PLAYER_HEIGHT
            if not self._collides_at(self.position.x, new_py, self.position.z):
                self.is_sneaking = False
                self.position.y = new_py
                self.camera_y_offset -= height_diff  # compensate, then lerps up
            else:
                self.effective_height = old_height

    # ================================================================== #
    #  Horizontal movement with wall collision + sneak edge guard          #
    # ================================================================== #
    def _try_move(self, dx, dz):
        """Move horizontally. When sneaking, prevent walking off edges."""
        # --- X axis ---
        if abs(dx) > 0.00001:
            new_x = self.position.x + dx
            if not self._collides_at(new_x, self.position.y, self.position.z):
                if (self.is_sneaking and self.is_on_ground
                        and not self._has_ground_below(new_x, self.position.z)):
                    self.move_speed = 0.0
                else:
                    self.position.x = new_x
            else:
                self.move_speed = 0.0

        # --- Z axis ---
        if abs(dz) > 0.00001:
            new_z = self.position.z + dz
            if not self._collides_at(self.position.x, self.position.y, new_z):
                if (self.is_sneaking and self.is_on_ground
                        and not self._has_ground_below(self.position.x, new_z)):
                    self.move_speed = 0.0
                else:
                    self.position.z = new_z
            else:
                self.move_speed = 0.0

    def _has_ground_below(self, px, pz):
        """True if there is solid ground below feet at (px, pz)."""
        return self._collides_at(px, self.position.y - 0.1, pz)

    # ================================================================== #
    #  Voxel lookup & AABB collision                                       #
    # ================================================================== #
    def _is_solid(self, x, y, z):
        fx, fy, fz = int(math.floor(x)), int(math.floor(y)), int(math.floor(z))
        cx, cy, cz = fx // CHUNK_SIZE, fy // CHUNK_SIZE, fz // CHUNK_SIZE
        if not (0 <= cx < WORLD_W and 0 <= cy < WORLD_H and 0 <= cz < WORLD_D):
            return False
        chunk_index = cx + WORLD_W * cz + WORLD_AREA * cy
        lx, ly, lz = fx % CHUNK_SIZE, fy % CHUNK_SIZE, fz % CHUNK_SIZE
        voxel_index = lx + CHUNK_SIZE * lz + CHUNK_AREA * ly
        return self.app.scene.world.voxels[chunk_index][voxel_index] != 0

    def _collides_at(self, px, py, pz):
        """Check AABB overlap with solid voxels, using effective_height."""
        half = PLAYER_WIDTH / 2.0 - COLLISION_SKIN
        min_x = int(math.floor(px - half))
        max_x = int(math.floor(px + half))
        min_z = int(math.floor(pz - half))
        max_z = int(math.floor(pz + half))
        min_y = int(math.floor(py - self.effective_height + COLLISION_SKIN))
        max_y = int(math.floor(py - COLLISION_SKIN))

        for bx in range(min_x, max_x + 1):
            for by in range(min_y, max_y + 1):
                for bz in range(min_z, max_z + 1):
                    if self._is_solid(bx, by, bz):
                        return True
        return False
