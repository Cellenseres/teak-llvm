declare i40 @llvm.umul.fix.i40(i40, i40, i32 immarg)
declare i40 @llvm.smul.fix.i40(i40, i40, i32 immarg)

define i16 @high_unsigned40(i16* %left, i16* %right, i16 %shift) {
  %left_middle = getelementptr i16, i16* %left, i16 1
  %left_high = getelementptr i16, i16* %left, i16 2
  %left0 = load i16, i16* %left
  %left1 = load i16, i16* %left_middle
  %left2 = load i16, i16* %left_high
  %left0_wide = zext i16 %left0 to i40
  %left1_wide = zext i16 %left1 to i40
  %left2_wide = zext i16 %left2 to i40
  %left1_shifted = shl i40 %left1_wide, 16
  %left2_shifted = shl i40 %left2_wide, 32
  %left_lower = or i40 %left0_wide, %left1_shifted
  %left_value = or i40 %left_lower, %left2_shifted
  %right_middle = getelementptr i16, i16* %right, i16 1
  %right_high = getelementptr i16, i16* %right, i16 2
  %right0 = load i16, i16* %right
  %right1 = load i16, i16* %right_middle
  %right2 = load i16, i16* %right_high
  %right0_wide = zext i16 %right0 to i40
  %right1_wide = zext i16 %right1 to i40
  %right2_wide = zext i16 %right2 to i40
  %right1_shifted = shl i40 %right1_wide, 16
  %right2_shifted = shl i40 %right2_wide, 32
  %right_lower = or i40 %right0_wide, %right1_shifted
  %right_value = or i40 %right_lower, %right2_shifted
  %high = call i40 @llvm.umul.fix.i40(i40 %left_value, i40 %right_value, i32 40)
  %shift_wide = zext i16 %shift to i40
  %shifted = lshr i40 %high, %shift_wide
  %result = trunc i40 %shifted to i16
  ret i16 %result
}

define i16 @divide_unsigned40(i16* %left, i16 %shift) {
  %left_middle = getelementptr i16, i16* %left, i16 1
  %left_high = getelementptr i16, i16* %left, i16 2
  %left0 = load i16, i16* %left
  %left1 = load i16, i16* %left_middle
  %left2 = load i16, i16* %left_high
  %left0_wide = zext i16 %left0 to i40
  %left1_wide = zext i16 %left1 to i40
  %left2_wide = zext i16 %left2 to i40
  %left1_shifted = shl i40 %left1_wide, 16
  %left2_shifted = shl i40 %left2_wide, 32
  %left_lower = or i40 %left0_wide, %left1_shifted
  %left_value = or i40 %left_lower, %left2_shifted
  %quotient = udiv i40 %left_value, 5
  %shift_wide = zext i16 %shift to i40
  %shifted = lshr i40 %quotient, %shift_wide
  %result = trunc i40 %shifted to i16
  ret i16 %result
}

define i16 @high_signed40(i16* %left, i16* %right, i16 %shift) {
  %left_middle = getelementptr i16, i16* %left, i16 1
  %left_high = getelementptr i16, i16* %left, i16 2
  %left0 = load i16, i16* %left
  %left1 = load i16, i16* %left_middle
  %left2 = load i16, i16* %left_high
  %left0_wide = zext i16 %left0 to i40
  %left1_wide = zext i16 %left1 to i40
  %left2_wide = zext i16 %left2 to i40
  %left1_shifted = shl i40 %left1_wide, 16
  %left2_shifted = shl i40 %left2_wide, 32
  %left_lower = or i40 %left0_wide, %left1_shifted
  %left_value = or i40 %left_lower, %left2_shifted
  %right_middle = getelementptr i16, i16* %right, i16 1
  %right_high = getelementptr i16, i16* %right, i16 2
  %right0 = load i16, i16* %right
  %right1 = load i16, i16* %right_middle
  %right2 = load i16, i16* %right_high
  %right0_wide = zext i16 %right0 to i40
  %right1_wide = zext i16 %right1 to i40
  %right2_wide = zext i16 %right2 to i40
  %right1_shifted = shl i40 %right1_wide, 16
  %right2_shifted = shl i40 %right2_wide, 32
  %right_lower = or i40 %right0_wide, %right1_shifted
  %right_value = or i40 %right_lower, %right2_shifted
  %scaled = call i40 @llvm.smul.fix.i40(i40 %left_value, i40 %right_value, i32 39)
  %shifted_high = ashr i40 %scaled, 1
  %left_minimum = icmp eq i40 %left_value, -549755813888
  %right_minimum = icmp eq i40 %right_value, -549755813888
  %positive_overflow = and i1 %left_minimum, %right_minimum
  %high = select i1 %positive_overflow, i40 274877906944, i40 %shifted_high
  %shift_wide = zext i16 %shift to i40
  %shifted = lshr i40 %high, %shift_wide
  %result = trunc i40 %shifted to i16
  ret i16 %result
}

define i16 @divide_signed40(i16* %left, i16 %shift) {
  %left_middle = getelementptr i16, i16* %left, i16 1
  %left_high = getelementptr i16, i16* %left, i16 2
  %left0 = load i16, i16* %left
  %left1 = load i16, i16* %left_middle
  %left2 = load i16, i16* %left_high
  %left0_wide = zext i16 %left0 to i40
  %left1_wide = zext i16 %left1 to i40
  %left2_wide = zext i16 %left2 to i40
  %left1_shifted = shl i40 %left1_wide, 16
  %left2_shifted = shl i40 %left2_wide, 32
  %left_lower = or i40 %left0_wide, %left1_shifted
  %left_value = or i40 %left_lower, %left2_shifted
  %quotient = sdiv i40 %left_value, 5
  %shift_wide = zext i16 %shift to i40
  %shifted = lshr i40 %quotient, %shift_wide
  %result = trunc i40 %shifted to i16
  ret i16 %result
}

define i16 @wide_constant40(i16 %index, i16 %shift) noinline optnone {
  switch i16 %index, label %constant0 [
    i16 1, label %constant1
    i16 2, label %constant2
    i16 3, label %constant3
    i16 4, label %constant4
    i16 5, label %constant5
    i16 6, label %constant6
    i16 7, label %constant7
    i16 8, label %constant8
    i16 9, label %constant9
    i16 10, label %constant10
    i16 11, label %constant11
    i16 12, label %constant12
    i16 13, label %constant13
    i16 14, label %constant14
    i16 15, label %constant15
    i16 16, label %constant16
    i16 17, label %constant17
    i16 18, label %constant18
    i16 19, label %constant19
    i16 20, label %constant20
    i16 21, label %constant21
    i16 22, label %constant22
    i16 23, label %constant23
    i16 24, label %constant24
    i16 25, label %constant25
    i16 26, label %constant26
    i16 27, label %constant27
    i16 28, label %constant28
    i16 29, label %constant29
    i16 30, label %constant30
    i16 31, label %constant31
    i16 32, label %constant32
    i16 33, label %constant33
    i16 34, label %constant34
    i16 35, label %constant35
    i16 36, label %constant36
    i16 37, label %constant37
    i16 38, label %constant38
    i16 39, label %constant39
    i16 40, label %constant40
    i16 41, label %constant41
    i16 42, label %constant42
    i16 43, label %constant43
    i16 44, label %constant44
    i16 45, label %constant45
    i16 46, label %constant46
    i16 47, label %constant47
    i16 48, label %constant48
    i16 49, label %constant49
    i16 50, label %constant50
    i16 51, label %constant51
    i16 52, label %constant52
    i16 53, label %constant53
    i16 54, label %constant54
    i16 55, label %constant55
    i16 56, label %constant56
    i16 57, label %constant57
    i16 58, label %constant58
    i16 59, label %constant59
    i16 60, label %constant60
    i16 61, label %constant61
    i16 62, label %constant62
    i16 63, label %constant63
    i16 64, label %constant64
    i16 65, label %constant65
    i16 66, label %constant66
    i16 67, label %constant67
    i16 68, label %constant68
    i16 69, label %constant69
    i16 70, label %constant70
    i16 71, label %constant71
    i16 72, label %constant72
    i16 73, label %constant73
    i16 74, label %constant74
    i16 75, label %constant75
    i16 76, label %constant76
    i16 77, label %constant77
    i16 78, label %constant78
    i16 79, label %constant79
    i16 80, label %constant80
    i16 81, label %constant81
    i16 82, label %constant82
    i16 83, label %constant83
    i16 84, label %constant84
    i16 85, label %constant85
    i16 86, label %constant86
    i16 87, label %constant87
    i16 88, label %constant88
    i16 89, label %constant89
    i16 90, label %constant90
    i16 91, label %constant91
    i16 92, label %constant92
    i16 93, label %constant93
    i16 94, label %constant94
    i16 95, label %constant95
    i16 96, label %constant96
    i16 97, label %constant97
    i16 98, label %constant98
    i16 99, label %constant99
    i16 100, label %constant100
    i16 101, label %constant101
    i16 102, label %constant102
    i16 103, label %constant103
    i16 104, label %constant104
    i16 105, label %constant105
    i16 106, label %constant106
    i16 107, label %constant107
    i16 108, label %constant108
    i16 109, label %constant109
  ]
constant0:
  br label %result
constant1:
  br label %result
constant2:
  br label %result
constant3:
  br label %result
constant4:
  br label %result
constant5:
  br label %result
constant6:
  br label %result
constant7:
  br label %result
constant8:
  br label %result
constant9:
  br label %result
constant10:
  br label %result
constant11:
  br label %result
constant12:
  br label %result
constant13:
  br label %result
constant14:
  br label %result
constant15:
  br label %result
constant16:
  br label %result
constant17:
  br label %result
constant18:
  br label %result
constant19:
  br label %result
constant20:
  br label %result
constant21:
  br label %result
constant22:
  br label %result
constant23:
  br label %result
constant24:
  br label %result
constant25:
  br label %result
constant26:
  br label %result
constant27:
  br label %result
constant28:
  br label %result
constant29:
  br label %result
constant30:
  br label %result
constant31:
  br label %result
constant32:
  br label %result
constant33:
  br label %result
constant34:
  br label %result
constant35:
  br label %result
constant36:
  br label %result
constant37:
  br label %result
constant38:
  br label %result
constant39:
  br label %result
constant40:
  br label %result
constant41:
  br label %result
constant42:
  br label %result
constant43:
  br label %result
constant44:
  br label %result
constant45:
  br label %result
constant46:
  br label %result
constant47:
  br label %result
constant48:
  br label %result
constant49:
  br label %result
constant50:
  br label %result
constant51:
  br label %result
constant52:
  br label %result
constant53:
  br label %result
constant54:
  br label %result
constant55:
  br label %result
constant56:
  br label %result
constant57:
  br label %result
constant58:
  br label %result
constant59:
  br label %result
constant60:
  br label %result
constant61:
  br label %result
constant62:
  br label %result
constant63:
  br label %result
constant64:
  br label %result
constant65:
  br label %result
constant66:
  br label %result
constant67:
  br label %result
constant68:
  br label %result
constant69:
  br label %result
constant70:
  br label %result
constant71:
  br label %result
constant72:
  br label %result
constant73:
  br label %result
constant74:
  br label %result
constant75:
  br label %result
constant76:
  br label %result
constant77:
  br label %result
constant78:
  br label %result
constant79:
  br label %result
constant80:
  br label %result
constant81:
  br label %result
constant82:
  br label %result
constant83:
  br label %result
constant84:
  br label %result
constant85:
  br label %result
constant86:
  br label %result
constant87:
  br label %result
constant88:
  br label %result
constant89:
  br label %result
constant90:
  br label %result
constant91:
  br label %result
constant92:
  br label %result
constant93:
  br label %result
constant94:
  br label %result
constant95:
  br label %result
constant96:
  br label %result
constant97:
  br label %result
constant98:
  br label %result
constant99:
  br label %result
constant100:
  br label %result
constant101:
  br label %result
constant102:
  br label %result
constant103:
  br label %result
constant104:
  br label %result
constant105:
  br label %result
constant106:
  br label %result
constant107:
  br label %result
constant108:
  br label %result
constant109:
  br label %result
result:
  %value = phi i40 [0, %constant0], [1, %constant1], [2, %constant2], [32767, %constant3], [32768, %constant4], [65535, %constant5], [65536, %constant6], [2147483647, %constant7], [2147483648, %constant8], [4294967295, %constant9], [4294967296, %constant10], [6361407414, %constant11], [9781322372, %constant12], [41693976738, %constant13], [46016195536, %constant14], [50395948634, %constant15], [58412016722, %constant16], [68570666328, %constant17], [74004965600, %constant18], [77229989188, %constant19], [77408386206, %constant20], [79740054194, %constant21], [81232739542, %constant22], [85802164026, %constant23], [110707297708, %constant24], [126809045032, %constant25], [132854424012, %constant26], [160105907292, %constant27], [167513333202, %constant28], [186877110816, %constant29], [191460388196, %constant30], [201052239618, %constant31], [203881030216, %constant32], [207474913036, %constant33], [232508984286, %constant34], [233353214448, %constant35], [256955187474, %constant36], [270530875978, %constant37], [317634666240, %constant38], [352105097720, %constant39], [355627838334, %constant40], [365157536054, %constant41], [368979447956, %constant42], [370544605302, %constant43], [371292057194, %constant44], [372410371736, %constant45], [391361483374, %constant46], [395558583124, %constant47], [415129291568, %constant48], [415150551852, %constant49], [439183067322, %constant50], [447333546318, %constant51], [468613629912, %constant52], [469933044522, %constant53], [471816995862, %constant54], [478444449958, %constant55], [490162874544, %constant56], [496352054716, %constant57], [496640313680, %constant58], [506539096036, %constant59], [517011722478, %constant60], [522324242152, %constant61], [539646692232, %constant62], [549755813887, %constant63], [549755813888, %constant64], [569114147610, %constant65], [584162305492, %constant66], [585040506250, %constant67], [600143583236, %constant68], [601574607702, %constant69], [607864759650, %constant70], [610093486756, %constant71], [642368281374, %constant72], [652564822542, %constant73], [654569126974, %constant74], [664951510010, %constant75], [682111608736, %constant76], [683591162558, %constant77], [697129560244, %constant78], [699270421766, %constant79], [712764312546, %constant80], [733482273244, %constant81], [742615277044, %constant82], [743726342252, %constant83], [744102957876, %constant84], [755356656690, %constant85], [762672509358, %constant86], [778615326922, %constant87], [796560565672, %constant88], [806010866242, %constant89], [811813462400, %constant90], [830681625800, %constant91], [838869668934, %constant92], [843904827456, %constant93], [857605610882, %constant94], [873526524560, %constant95], [875590606630, %constant96], [917070461070, %constant97], [918327397116, %constant98], [933264828188, %constant99], [984365128824, %constant100], [993815169926, %constant101], [999542149530, %constant102], [1003087135544, %constant103], [1011011844074, %constant104], [1030102094988, %constant105], [1033040154748, %constant106], [1072101959538, %constant107], [1076346030054, %constant108], [1099511627775, %constant109]
  %shift_wide = zext i16 %shift to i40
  %shifted = lshr i40 %value, %shift_wide
  %result_word = trunc i40 %shifted to i16
  ret i16 %result_word
}
