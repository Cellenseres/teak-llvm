declare i40 @state_high_product(i40, i40, i16*, i16) addrspace(1)
declare i40 @state_low_product(i40, i40, i16*, i16) addrspace(1)
declare i40 @state_word_product(i40, i40, i16*, i16) addrspace(1)
; SPDX-License-Identifier: BSD-2-Clause
declare i40 @__teak_mulword40(i40, i40) addrspace(1) nounwind readnone

define i16 @word_product40(i16* %input, i16 %factor, i16 %shift) addrspace(1) {
  %middle = getelementptr i16, i16* %input, i16 1
  %high = getelementptr i16, i16* %input, i16 2
  %word0 = load i16, i16* %input
  %word1 = load i16, i16* %middle
  %word2 = load i16, i16* %high
  %low_wide = zext i16 %word0 to i40
  %middle_wide = zext i16 %word1 to i40
  %high_wide = zext i16 %word2 to i40
  %middle_bits = shl i40 %middle_wide, 16
  %high_bits = shl i40 %high_wide, 32
  %lower = or i40 %low_wide, %middle_bits
  %value = or i40 %lower, %high_bits
  %signed_factor = sext i16 %factor to i40
  %product = mul i40 %value, %signed_factor
  %wide_shift = zext i16 %shift to i40
  %shifted = lshr i40 %product, %wide_shift
  %result = trunc i40 %shifted to i16
  ret i16 %result
}

define i16 @word_product_left40(i16* %input, i16 %factor, i16 %shift) addrspace(1) {
  %middle = getelementptr i16, i16* %input, i16 1
  %high = getelementptr i16, i16* %input, i16 2
  %word0 = load i16, i16* %input
  %word1 = load i16, i16* %middle
  %word2 = load i16, i16* %high
  %low_wide = zext i16 %word0 to i40
  %middle_wide = zext i16 %word1 to i40
  %high_wide = zext i16 %word2 to i40
  %middle_bits = shl i40 %middle_wide, 16
  %high_bits = shl i40 %high_wide, 32
  %lower = or i40 %low_wide, %middle_bits
  %value = or i40 %lower, %high_bits
  %signed_factor = sext i16 %factor to i40
  %product = mul i40 %signed_factor, %value
  %wide_shift = zext i16 %shift to i40
  %shifted = lshr i40 %product, %wide_shift
  %result = trunc i40 %shifted to i16
  ret i16 %result
}

define i16 @word_product_direct40(i16* %input, i16 %factor, i16 %shift) addrspace(1) {
  %middle = getelementptr i16, i16* %input, i16 1
  %high = getelementptr i16, i16* %input, i16 2
  %word0 = load i16, i16* %input
  %word1 = load i16, i16* %middle
  %word2 = load i16, i16* %high
  %low_wide = zext i16 %word0 to i40
  %middle_wide = zext i16 %word1 to i40
  %high_wide = zext i16 %word2 to i40
  %middle_bits = shl i40 %middle_wide, 16
  %high_bits = shl i40 %high_wide, 32
  %lower = or i40 %low_wide, %middle_bits
  %value = or i40 %lower, %high_bits
  %signed_factor = sext i16 %factor to i40
  %product = call addrspace(1) i40 @__teak_mulword40(i40 %value, i40 %signed_factor)
  %wide_shift = zext i16 %shift to i40
  %shifted = lshr i40 %product, %wide_shift
  %result = trunc i40 %shifted to i16
  ret i16 %result
}

define i16 @state_word_product40(i16* %input, i16 %factor, i16 %shift, i16* %state, i16 %interrupts) addrspace(1) {
  %middle = getelementptr i16, i16* %input, i16 1
  %high = getelementptr i16, i16* %input, i16 2
  %word0 = load i16, i16* %input
  %word1 = load i16, i16* %middle
  %word2 = load i16, i16* %high
  %low_wide = zext i16 %word0 to i40
  %middle_wide = zext i16 %word1 to i40
  %high_wide = zext i16 %word2 to i40
  %middle_bits = shl i40 %middle_wide, 16
  %high_bits = shl i40 %high_wide, 32
  %lower = or i40 %low_wide, %middle_bits
  %value = or i40 %lower, %high_bits
  %signed_factor = sext i16 %factor to i40
  %product = call addrspace(1) i40 @state_word_product(i40 %value, i40 %signed_factor, i16* %state, i16 %interrupts)
  %wide_shift = zext i16 %shift to i40
  %shifted = lshr i40 %product, %wide_shift
  %result = trunc i40 %shifted to i16
  ret i16 %result
}

define i16 @state_low_product40(i16* %input, i16 %factor, i16 %shift, i16* %state, i16 %interrupts) addrspace(1) {
  %middle = getelementptr i16, i16* %input, i16 1
  %high = getelementptr i16, i16* %input, i16 2
  %word0 = load i16, i16* %input
  %word1 = load i16, i16* %middle
  %word2 = load i16, i16* %high
  %low_wide = zext i16 %word0 to i40
  %middle_wide = zext i16 %word1 to i40
  %high_wide = zext i16 %word2 to i40
  %middle_bits = shl i40 %middle_wide, 16
  %high_bits = shl i40 %high_wide, 32
  %lower = or i40 %low_wide, %middle_bits
  %value = or i40 %lower, %high_bits
  %signed_factor = sext i16 %factor to i40
  %product = call addrspace(1) i40 @state_low_product(i40 %value, i40 %signed_factor, i16* %state, i16 %interrupts)
  %wide_shift = zext i16 %shift to i40
  %shifted = lshr i40 %product, %wide_shift
  %result = trunc i40 %shifted to i16
  ret i16 %result
}

define i16 @state_high_product40(i16* %input, i16 %factor, i16 %shift, i16* %state, i16 %interrupts) addrspace(1) {
  %middle = getelementptr i16, i16* %input, i16 1
  %high = getelementptr i16, i16* %input, i16 2
  %word0 = load i16, i16* %input
  %word1 = load i16, i16* %middle
  %word2 = load i16, i16* %high
  %low_wide = zext i16 %word0 to i40
  %middle_wide = zext i16 %word1 to i40
  %high_wide = zext i16 %word2 to i40
  %middle_bits = shl i40 %middle_wide, 16
  %high_bits = shl i40 %high_wide, 32
  %lower = or i40 %low_wide, %middle_bits
  %value = or i40 %lower, %high_bits
  %signed_factor = sext i16 %factor to i40
  %product = call addrspace(1) i40 @state_high_product(i40 %value, i40 %signed_factor, i16* %state, i16 %interrupts)
  %wide_shift = zext i16 %shift to i40
  %shifted = lshr i40 %product, %wide_shift
  %result = trunc i40 %shifted to i16
  ret i16 %result
}
