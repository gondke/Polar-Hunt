import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from fractions import Fraction
import random

# =========================================================
# PAGE CONFIGURATION & STYLING
# =========================================================
st.set_page_config(
    page_title="2D Vector Rotation Target Game",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast CSS Theme
st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .calc-box {
        background-color: #090d16;
        border-left: 4px solid #00f0ff;
        padding: 12px;
        font-family: monospace;
        color: #00f0ff;
        border-radius: 4px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# GAME STATE INITIALIZATION
# =========================================================
ALLOWED_ANGLES = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]

def reset_game():
    # Pick target angle phi on unit circle (a = 1)
    target_deg = random.choice(ALLOWED_ANGLES) * random.choice([1, -1])
    target_deg = target_deg % 360
    
    # Pick an initial vector angle such that AT LEAST ONE combination hits the target
    valid_theta = random.choice(ALLOWED_ANGLES)
    matrix_type = random.choice(['A', 'A_T'])
    
    # Target = Vector rotated by Matrix(theta)
    # So initial vector angle = Target angle - (+/- theta)
    if matrix_type == 'A':
        # Matrix A rotates CLOCKWISE by theta -> v_target_angle = v_init_angle - theta
        init_deg = (target_deg + valid_theta) % 360
    else:
        # Matrix A^T rotates COUNTER-CLOCKWISE by theta -> v_target_angle = v_init_angle + theta
        init_deg = (target_deg - valid_theta) % 360
        
    st.session_state.target_angle = target_deg
    st.session_state.init_angle = init_deg
    st.session_state.attempts_left = 2
    st.session_state.game_over = False
    st.session_state.current_vector = np.array([np.cos(np.radians(init_deg)), np.sin(np.radians(init_deg))])
    st.session_state.history = []

if 'target_angle' not in st.session_state:
    reset_game()

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def to_frac_str(val, max_denom=1000):
    if abs(val) < 1e-7:
        return "0"
    frac = Fraction(val).limit_denominator(max_denom)
    if frac.denominator == 1:
        return f"{frac.numerator}"
    if frac.numerator < 0:
        return f"-{abs(frac.numerator)}/{frac.denominator}"
    return f"{frac.numerator}/{frac.denominator}"

def get_rotation_matrix(theta_deg, matrix_type):
    rad = np.radians(theta_deg)
    c, s = np.cos(rad), np.sin(rad)
    
    # Specified Matrix A = [[cos, sin], [-sin, cos]]
    if matrix_type == "A":
        return np.array([[c, s], [-s, c]])
    else:
        # Transpose A^T = [[cos, -sin], [sin, cos]]
        return np.array([[c, -s], [s, c]])

# =========================================================
# SIDEBAR CONTROLS
# =========================================================
st.sidebar.title("🎯 Target Controls")
st.sidebar.write("Rotate the unit vector to hit the red star target on $x^2+y^2=1$!")

st.sidebar.markdown(f"### **Attempts Left:** `{st.session_state.attempts_left} / 2`")

# Inputs
selected_matrix = st.sidebar.radio(
    "1. Select Transformation Matrix:",
    options=["A", "A^T"],
    help="Matrix A rotates CW; Matrix A^T rotates CCW."
)

selected_theta = st.sidebar.selectbox(
    "2. Select Rotation Angle θ (Degrees):",
    options=ALLOWED_ANGLES,
    index=0
)

col_btn1, col_btn2 = st.sidebar.columns(2)
submit_move = col_btn1.button("🚀 Fire Vector", use_container_width=True)
reset_btn = col_btn2.button("🔄 New Game", use_container_width=True)

if reset_btn:
    reset_game()
    st.rerun()

# =========================================================
# GAME LOGIC EXECUTION
# =========================================================
matrix_code = "A" if selected_matrix == "A" else "A_T"
M = get_rotation_matrix(selected_theta, matrix_code)

if submit_move and not st.session_state.game_over:
    # Compute new rotated vector
    new_v = np.dot(M, st.session_state.current_vector)
    st.session_state.current_vector = new_v
    st.session_state.attempts_left -= 1
    
    # Calculate current angle
    curr_angle = np.degrees(np.arctan2(new_v[1], new_v[0])) % 360
    target_angle = st.session_state.target_angle % 360
    
    # Check hit (with floating point tolerance)
    angle_diff = abs(curr_angle - target_angle)
    if angle_diff < 1e-2 or abs(angle_diff - 360) < 1e-2:
        st.balloons()
        st.success("🎉 **Congratulations...! You Won!**")
        st.session_state.game_over = True
    else:
        if st.session_state.attempts_left == 0:
            st.error(f"❌ **Game Over! You lost.** Target was at {target_angle:.0f}°. Resetting game...")
            st.session_state.game_over = True
        else:
            st.warning("⚠️ Missed target! Try again with your remaining attempt.")

# =========================================================
# PLOTTING GAME GRID (MATPLOTLIB)
# =========================================================
fig, ax = plt.subplots(figsize=(7, 7), facecolor="#0d1117")
ax.set_facecolor("#0d1117")

# 1. Canvas Boundary setup (-5 to +5 cm equivalent)
GRID_BOUND = 5.0
ax.set_xlim(-GRID_BOUND, GRID_BOUND)
ax.set_ylim(-GRID_BOUND, GRID_BOUND)
ax.set_aspect('equal')

# 2. Cartesian Lattice Grid
ax.xaxis.set_major_locator(MultipleLocator(1))
ax.yaxis.set_major_locator(MultipleLocator(1))
ax.grid(True, which='major', color='#21262d', linestyle='-', linewidth=0.8)
ax.axhline(0, color='#8b949e', linewidth=1.2)
ax.axvline(0, color='#8b949e', linewidth=1.2)

# 3. Polar Grid Overlay (Cyan) & Concentric Circles (a = 1, 2, 3)
angles_rad = np.radians(np.arange(0, 360, 30))
for r in [1, 2, 3]:
    circle = plt.Circle((0, 0), r, color='#00f0ff', fill=False, linestyle='--', alpha=0.5, linewidth=1.2)
    ax.add_patch(circle)
    ax.text(r * np.cos(np.pi/4) + 0.1, r * np.sin(np.pi/4) + 0.1, f'a={r}', color='#00f0ff', fontsize=8)

for ang in angles_rad:
    ax.plot([0, 4.5 * np.cos(ang)], [0, 4.5 * np.sin(ang)], color='#00f0ff', linestyle=':', alpha=0.3, linewidth=0.8)

# 4. Plot Target (Red Star on a = 1 circle)
target_rad = np.radians(st.session_state.target_angle)
tx, ty = np.cos(target_rad), np.sin(target_rad)
ax.plot(tx, ty, marker='*', markersize=18, color='#ff0055', markeredgecolor='white', label=f'Target ({st.session_state.target_angle:.0f}°)')

# 5. Plot Initial Vector Reference (Faded Ghost)
init_rad = np.radians(st.session_state.init_angle)
ix, iy = np.cos(init_rad), np.sin(init_rad)
ax.quiver(0, 0, ix, iy, angles='xy', scale_units='xy', scale=1, color='#8b949e', alpha=0.4, label='Initial Position')

# 6. Plot Current/Rotated Vector
cv = st.session_state.current_vector
ax.quiver(0, 0, cv[0], cv[1], angles='xy', scale_units='xy', scale=1, color='#00ff66', width=0.015, label='Current Vector')

# Formatting labels
ax.set_title("10 cm × 10 cm Dual Cartesian-Polar Coordinate System", color="white", fontsize=12, pad=12)
ax.tick_params(colors='#8b949e')
for spine in ax.spines.values():
    spine.set_color('#30363d')
ax.legend(loc='upper right', facecolor='#161b22', edgecolor='#30363d', labelcolor='white')

# =========================================================
# MAIN LAYOUT RENDERING
# =========================================================
st.title("⚡ 2D Vector Rotation Target Game")

col_plot, col_math = st.columns([1.1, 0.9])

with col_plot:
    st.pyplot(fig)

with col_math:
    st.markdown("### 🧮 Live Matrix Calculation")
    
    # Live Matrix Representation
    c_str, s_str = to_frac_str(M[0,0]), to_frac_str(M[0,1])
    ms1, ms2 = to_frac_str(M[1,0]), to_frac_str(M[1,1])
    
    vx_str = to_frac_str(st.session_state.current_vector[0])
    vy_str = to_frac_str(st.session_state.current_vector[1])

    st.markdown(f"""
    <div class="metric-card">
        <h4>Selected Operator Matrix ({selected_matrix}):</h4>
        <div class="calc-box">
            [{c_str:>8}  {s_str:>8}] <br>
            [{ms1:>8}  {ms2:>8}]
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="metric-card">
        <h4>Current Vector Position:</h4>
        <div class="calc-box">
            v = [{st.session_state.current_vector[0]:.4f}, {st.session_state.current_vector[1]:.4f}]ᵀ
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metric-card">
        <h4>Target Coordinate Goal:</h4>
        <div class="calc-box" style="color: #ff0055; border-left-color: #ff0055;">
            Target = [{tx:.4f}, {ty:.4f}]ᵀ  ({st.session_state.target_angle:.0f}°)
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.game_over and st.session_state.attempts_left == 0:
        if st.button("🔄 Play Again", type="primary", use_container_width=True):
            reset_game()
            st.rerun()
