; SPDX-License-Identifier: BSD-2-Clause
target datalayout = "E-m:e-P1-p0:16:16:16-p1:32:32:32-i1:16:16-i8:16:16-i16:16:16-i32:32:32-a:0:32-n16:40"
target triple = "teak"

define i16 @divide40(i16* %input, i16 %operation, i16 %shift) addrspace(1) {
  %a0 = load volatile i16, i16* %input
  %p1 = getelementptr i16, i16* %input, i16 1
  %a1 = load volatile i16, i16* %p1
  %p2 = getelementptr i16, i16* %input, i16 2
  %a2 = load volatile i16, i16* %p2
  %p3 = getelementptr i16, i16* %input, i16 3
  %b0 = load volatile i16, i16* %p3
  %p4 = getelementptr i16, i16* %input, i16 4
  %b1 = load volatile i16, i16* %p4
  %p5 = getelementptr i16, i16* %input, i16 5
  %b2 = load volatile i16, i16* %p5
  %a0wide = zext i16 %a0 to i40
  %a1wide = zext i16 %a1 to i40
  %a2wide = zext i16 %a2 to i40
  %a1shift = shl i40 %a1wide, 16
  %a2shift = shl i40 %a2wide, 32
  %alow = or i40 %a0wide, %a1shift
  %left = or i40 %alow, %a2shift
  %b0wide = zext i16 %b0 to i40
  %b1wide = zext i16 %b1 to i40
  %b2wide = zext i16 %b2 to i40
  %b1shift = shl i40 %b1wide, 16
  %b2shift = shl i40 %b2wide, 32
  %blow = or i40 %b0wide, %b1shift
  %right = or i40 %blow, %b2shift
  switch i16 %operation, label %unsigned_divide [i16 1, label %unsigned_remainder
    i16 2, label %signed_divide
    i16 3, label %signed_remainder]
unsigned_divide:
  %uq = udiv i40 %left, %right
  br label %exit
unsigned_remainder:
  %ur = urem i40 %left, %right
  br label %exit
signed_divide:
  %sq = sdiv i40 %left, %right
  br label %exit
signed_remainder:
  %sr = srem i40 %left, %right
  br label %exit
exit:
  %result = phi i40 [%uq, %unsigned_divide], [%ur, %unsigned_remainder], [%sq, %signed_divide], [%sr, %signed_remainder]
  %wide_shift = zext i16 %shift to i40
  %shifted = lshr i40 %result, %wide_shift
  %word = trunc i40 %shifted to i16
  ret i16 %word
}
