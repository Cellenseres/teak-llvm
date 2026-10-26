declare i40 @llvm.ctlz.i40(i40, i1 immarg)
declare i16 @llvm.ctlz.i16(i16, i1 immarg)

define i16 @leading_zeroes16(i16 %value) {
  %count = call i16 @llvm.ctlz.i16(i16 %value, i1 false)
  ret i16 %count
}

define i16 @leading_zeroes40(i16 %low_word, i16 %middle_word, i16 %high_word) {
  %low = zext i16 %low_word to i40
  %middle = zext i16 %middle_word to i40
  %high = zext i16 %high_word to i40
  %middle_shifted = shl i40 %middle, 16
  %high_shifted = shl i40 %high, 32
  %lower_bits = or i40 %low, %middle_shifted
  %value = or i40 %lower_bits, %high_shifted
  %count = call i40 @llvm.ctlz.i40(i40 %value, i1 false)
  %result = trunc i40 %count to i16
  ret i16 %result
}
