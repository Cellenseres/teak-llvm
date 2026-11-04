; SPDX-License-Identifier: BSD-2-Clause
target datalayout = "E-m:e-P1-p0:16:16:16-p1:32:32:32-i1:16:16-i8:16:16-i16:16:16-i32:32:32-a:0:32-n16:40"
target triple = "teak"

declare i40 @__teak_divmod40(i40, i40, i16) addrspace(1) #0

define i40 @__teak_udiv40(i40 %numerator, i40 %divisor) addrspace(1) #1 {
  %result = call addrspace(1) i40 @__teak_divmod40(i40 %numerator, i40 %divisor, i16 0)
  ret i40 %result
}

define i40 @__teak_urem40(i40 %numerator, i40 %divisor) addrspace(1) #1 {
  %result = call addrspace(1) i40 @__teak_divmod40(i40 %numerator, i40 %divisor, i16 1)
  ret i40 %result
}

define i40 @__teak_sdiv40(i40 %numerator, i40 %divisor) addrspace(1) #1 {
  %left_sign = ashr i40 %numerator, 39
  %right_sign = ashr i40 %divisor, 39
  %left_bits = xor i40 %numerator, %left_sign
  %right_bits = xor i40 %divisor, %right_sign
  %left_magnitude = sub i40 %left_bits, %left_sign
  %right_magnitude = sub i40 %right_bits, %right_sign
  %quotient = call addrspace(1) i40 @__teak_divmod40(i40 %left_magnitude, i40 %right_magnitude, i16 0)
  %result_sign = xor i40 %left_sign, %right_sign
  %result_bits = xor i40 %quotient, %result_sign
  %result = sub i40 %result_bits, %result_sign
  ret i40 %result
}

define i40 @__teak_srem40(i40 %numerator, i40 %divisor) addrspace(1) #1 {
  %left_sign = ashr i40 %numerator, 39
  %right_sign = ashr i40 %divisor, 39
  %left_bits = xor i40 %numerator, %left_sign
  %right_bits = xor i40 %divisor, %right_sign
  %left_magnitude = sub i40 %left_bits, %left_sign
  %right_magnitude = sub i40 %right_bits, %right_sign
  %remainder = call addrspace(1) i40 @__teak_divmod40(i40 %left_magnitude, i40 %right_magnitude, i16 1)
  %result_bits = xor i40 %remainder, %left_sign
  %result = sub i40 %result_bits, %left_sign
  ret i40 %result
}

attributes #0 = { noinline nounwind readnone }
attributes #1 = { nounwind readnone }
!0 = distinct !{!0, !1}
!1 = !{!"llvm.loop.unroll.disable"}
