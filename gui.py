import dearpygui.dearpygui as dpg
from datetime import datetime
from common import state_continue, state_no_quote, state_stop_loss, state_stop_retrace, state_stop_hold, get_3_prices, \
    should_sell

def save_callback():
    print("Save Clicked")

dpg.create_context()
dpg.create_viewport()
dpg.setup_dearpygui()

stock = '1.600800'
buy_date = datetime(2022, 3, 18)
buy_price = 5.08
max_hold_days = 9
hold_days, highest, lowest, lowest_aft_highest, = get_3_prices(stock, buy_date)

with dpg.window(label="Example Window"):
    dpg.add_text("Hello world")
    dpg.add_button(label="Save", callback=save_callback)
    dpg.add_input_text(label="string")
    dpg.add_slider_float(label="float")

dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()