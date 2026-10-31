; SPDX-License-Identifier: BSD-2-Clause
target datalayout = "E-m:e-P1-p0:16:16:16-p1:32:32:32-i1:16:16-i8:16:16-i16:16:16-i32:32:32-a:0:32-n16:40"
target triple = "teak"

declare i40 @llvm.ctlz.i40(i40, i1 immarg)

define internal i40 @unsigned_divide40(i40 %numerator, i40 %divisor, i16 %want_remainder) addrspace(1) #0 {
entry:
  %smaller = icmp ult i40 %numerator, %divisor
  br i1 %smaller, label %exit, label %prepare
prepare:
  %numerator_zeroes = call i40 @llvm.ctlz.i40(i40 %numerator, i1 false)
  %divisor_zeroes = call i40 @llvm.ctlz.i40(i40 %divisor, i1 false)
  %shift = sub i40 %divisor_zeroes, %numerator_zeroes
  %initial_divisor = shl i40 %divisor, %shift
  %initial_mask = shl i40 1, %shift
  br label %loop
loop:
  %aligned_divisor = phi i40 [%initial_divisor, %prepare], [%next_divisor, %loop]
  %mask = phi i40 [%initial_mask, %prepare], [%next_mask, %loop]
  %quotient = phi i40 [0, %prepare], [%next_quotient, %loop]
  %remainder = phi i40 [%numerator, %prepare], [%next_remainder, %loop]
  %fits = icmp uge i40 %remainder, %aligned_divisor
  %difference = sub i40 %remainder, %aligned_divisor
  %next_remainder = select i1 %fits, i40 %difference, i40 %remainder
  %quotient_bit = select i1 %fits, i40 %mask, i40 0
  %next_quotient = or i40 %quotient, %quotient_bit
  %next_divisor = lshr i40 %aligned_divisor, 1
  %next_mask = lshr i40 %mask, 1
  %finished = icmp eq i40 %next_mask, 0
  br i1 %finished, label %exit, label %loop, !llvm.loop !0
exit:
  %final_quotient = phi i40 [0, %entry], [%next_quotient, %loop]
  %final_remainder = phi i40 [%numerator, %entry], [%next_remainder, %loop]
  %select_remainder = icmp ne i16 %want_remainder, 0
  %result = select i1 %select_remainder, i40 %final_remainder, i40 %final_quotient
  ret i40 %result
}

define i40 @__teak_udiv40(i40 %numerator, i40 %divisor) addrspace(1) #1 {
  %result = call addrspace(1) i40 @unsigned_divide40(i40 %numerator, i40 %divisor, i16 0)
  ret i40 %result
}

define i40 @__teak_urem40(i40 %numerator, i40 %divisor) addrspace(1) #1 {
  %result = call addrspace(1) i40 @unsigned_divide40(i40 %numerator, i40 %divisor, i16 1)
  ret i40 %result
}

define i40 @__teak_sdiv40(i40 %numerator, i40 %divisor) addrspace(1) #1 {
  %left_sign = ashr i40 %numerator, 39
  %right_sign = ashr i40 %divisor, 39
  %left_bits = xor i40 %numerator, %left_sign
  %right_bits = xor i40 %divisor, %right_sign
  %left_magnitude = sub i40 %left_bits, %left_sign
  %right_magnitude = sub i40 %right_bits, %right_sign
  %quotient = call addrspace(1) i40 @unsigned_divide40(i40 %left_magnitude, i40 %right_magnitude, i16 0)
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
  %remainder = call addrspace(1) i40 @unsigned_divide40(i40 %left_magnitude, i40 %right_magnitude, i16 1)
  %result_bits = xor i40 %remainder, %left_sign
  %result = sub i40 %result_bits, %left_sign
  ret i40 %result
}

attributes #0 = { noinline nounwind readnone }
attributes #1 = { nounwind readnone }
!0 = distinct !{!0, !1}
!1 = !{!"llvm.loop.unroll.disable"}
