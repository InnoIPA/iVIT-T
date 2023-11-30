#!/bin/bash

# Function to draw the progress bar
draw_progress_bar() {
  local progress=$1
  local bar_length=50
  local filled_length=$((progress * bar_length / 100))
  local empty_length=$((bar_length - filled_length))

  # Draw the progress bar
  printf "["
  printf "%*s" $filled_length | tr ' ' '='
  printf "%*s" $empty_length | tr ' ' ' '
  printf "] %d%%\r" $progress
}

