define i16 @multiply40(i16* %left, i16* %right, i16 %shift) {
  %left_middle = getelementptr i16, i16* %left, i16 1
  %left_high = getelementptr i16, i16* %left, i16 2
  %right_middle = getelementptr i16, i16* %right, i16 1
  %right_high = getelementptr i16, i16* %right, i16 2
  %left0 = load i16, i16* %left
  %left1 = load i16, i16* %left_middle
  %left2 = load i16, i16* %left_high
  %right0 = load i16, i16* %right
  %right1 = load i16, i16* %right_middle
  %right2 = load i16, i16* %right_high
  %left0_wide = zext i16 %left0 to i40
  %left1_wide = zext i16 %left1 to i40
  %left2_wide = zext i16 %left2 to i40
  %right0_wide = zext i16 %right0 to i40
  %right1_wide = zext i16 %right1 to i40
  %right2_wide = zext i16 %right2 to i40
  %left1_shifted = shl i40 %left1_wide, 16
  %left2_shifted = shl i40 %left2_wide, 32
  %right1_shifted = shl i40 %right1_wide, 16
  %right2_shifted = shl i40 %right2_wide, 32
  %left_lower = or i40 %left0_wide, %left1_shifted
  %left_value = or i40 %left_lower, %left2_shifted
  %right_lower = or i40 %right0_wide, %right1_shifted
  %right_value = or i40 %right_lower, %right2_shifted
  %product = mul i40 %left_value, %right_value
  %shift_wide = zext i16 %shift to i40
  %shifted = lshr i40 %product, %shift_wide
  %result = trunc i40 %shifted to i16
  ret i16 %result
}

define i16 @multiply_signed40(i16* %left, i16* %right, i16 %shift) {
  %right_middle = getelementptr i16, i16* %right, i16 1
  %right_high = getelementptr i16, i16* %right, i16 2
  %left0 = load i16, i16* %left
  %right0 = load i16, i16* %right
  %right1 = load i16, i16* %right_middle
  %right2 = load i16, i16* %right_high
  %left0_wide = sext i16 %left0 to i40
  %right0_wide = zext i16 %right0 to i40
  %right1_wide = zext i16 %right1 to i40
  %right2_wide = zext i16 %right2 to i40
  %right1_shifted = shl i40 %right1_wide, 16
  %right2_shifted = shl i40 %right2_wide, 32
  %right_lower = or i40 %right0_wide, %right1_shifted
  %right_value = or i40 %right_lower, %right2_shifted
  %product = mul i40 %left0_wide, %right_value
  %shift_wide = zext i16 %shift to i40
  %shifted = lshr i40 %product, %shift_wide
  %result = trunc i40 %shifted to i16
  ret i16 %result
}
