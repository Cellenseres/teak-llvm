//===-- TeakISelLowering.cpp - Teak DAG Lowering Implementation ---------===//
//
//                     The LLVM Compiler Infrastructure
//
// This file is distributed under the University of Illinois Open Source
// License. See LICENSE.TXT for details.
//
//===----------------------------------------------------------------------===//
//
// This file implements the TeakTargetLowering class.
//
//===----------------------------------------------------------------------===//

#include "TeakISelLowering.h"
#include "Teak.h"
#include "TeakMachineFunctionInfo.h"
#include "TeakSubtarget.h"
#include "TeakTargetMachine.h"
#include "llvm/CodeGen/CallingConvLower.h"
#include "llvm/CodeGen/MachineFrameInfo.h"
#include "llvm/CodeGen/MachineFunction.h"
#include "llvm/CodeGen/MachineInstrBuilder.h"
#include "llvm/CodeGen/MachineJumpTableInfo.h"
#include "llvm/CodeGen/MachineRegisterInfo.h"
#include "llvm/CodeGen/SelectionDAGISel.h"
#include "llvm/CodeGen/TargetLoweringObjectFileImpl.h"
#include "llvm/CodeGen/ValueTypes.h"
#include "llvm/IR/CallingConv.h"
#include "llvm/IR/Constants.h"
#include "llvm/IR/DerivedTypes.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/GlobalAlias.h"
#include "llvm/IR/GlobalVariable.h"
#include "llvm/IR/Intrinsics.h"
#include "llvm/Support/Debug.h"
#include "llvm/Support/ErrorHandling.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Support/Signals.h"

using namespace llvm;

const char *TeakTargetLowering::getTargetNodeName(unsigned Opcode) const {
  switch (Opcode) {
  default:
	return NULL;
  case TeakISD::RET_FLAG:
	return "RetFlag";
  case TeakISD::LOAD_SYM:
	return "LOAD_SYM";
  case TeakISD::MOVEi32:
	return "MOVEi32";
  case TeakISD::CALL:
	return "CALL";
  }
}

MVT TeakTargetLowering::getScalarShiftAmountTy(const DataLayout &DL,
											   EVT) const {
  return MVT::i40;
}

EVT TeakTargetLowering::getSetCCResultType(const DataLayout &, LLVMContext &, EVT VT) const {
  return MVT::i40;
} 

TeakTargetLowering::TeakTargetLowering(const TeakTargetMachine &TeakTM)
	: TargetLowering(TeakTM), Subtarget(*TeakTM.getSubtargetImpl())
{
	setBooleanContents(ZeroOrOneBooleanContent);
  	setBooleanVectorContents(ZeroOrOneBooleanContent);
	// Set up the register classes.
	//addRegisterClass(MVT::i16, &Teak::GRRegsRegClass);
	addRegisterClass(MVT::i16, &Teak::ABLRegsRegClass);
	//addRegisterClass(MVT::i16, &Teak::ALRegsRegClass);
	addRegisterClass(MVT::i16, &Teak::RegNoBRegs16_nohRegClass);
	// addRegisterClass(MVT::i16, &Teak::RegNoBRegs16_noh_pageRegClass);
	//addRegisterClass(MVT::i16, &Teak::Y0RegsRegClass);
	//addRegisterClass(MVT::i32, &Teak::P0RegsRegClass);
	//addRegisterClass(MVT::i16, &Teak::ABHRegsRegClass);
	//addRegisterClass(MVT::i16, &Teak::ABLRegsRegClass);
	//addRegisterClass(MVT::i16, &Teak::ABHRegsRegClass);

	// addRegisterClass(MVT::i16, &Teak::RegNoBRegs16RegClass);
	//addRegisterClass(MVT::i40, &Teak::RegNoBRegs40RegClass);
	addRegisterClass(MVT::i40, &Teak::ABRegsRegClass);
	//addRegisterClass(MVT::i40, &Teak::ARegsRegClass);
	//addRegisterClass(MVT::i40, &Teak::BRegsRegClass);



	// Compute derived properties from the register classes
	computeRegisterProperties(Subtarget.getRegisterInfo());
	
	//for (unsigned Op = 0; Op < ISD::BUILTIN_OP_END; ++Op)
    //  	setOperationAction(Op, MVT::i32, Expand);

	//setOperationAction(ISD::MUL, MVT::i16, Legal);
	//setOperationAction(ISD::MUL, MVT::i32, Legal);
	//setOperationAction(ISD::MUL, MVT::i40, Expand);

	setOperationAction(ISD::ADD, MVT::i16, Custom);
	setOperationAction(ISD::SUB, MVT::i16, Custom);
	setOperationAction(ISD::MUL, MVT::i16, Custom);
	setOperationAction(ISD::MUL, MVT::i40, Custom);
	setOperationAction(ISD::MULHU, MVT::i40, Custom);
	setOperationAction(ISD::MULHS, MVT::i40, Custom);
	setOperationAction(ISD::MULHU, MVT::i16, Expand);
	setOperationAction(ISD::MULHS, MVT::i16, Expand);
	setOperationAction(ISD::UMUL_LOHI, MVT::i40, Expand);
	setOperationAction(ISD::SMUL_LOHI, MVT::i40, Expand);
	setOperationAction(ISD::UMUL_LOHI, MVT::i16, Expand);
	setOperationAction(ISD::SMUL_LOHI, MVT::i16, Expand);
	for (MVT ValueType : {MVT::i16, MVT::i40}) {
		for (unsigned Opcode : {ISD::UDIV, ISD::UREM, ISD::SDIV, ISD::SREM})
			setOperationAction(Opcode, ValueType, Custom);
		setOperationAction(ISD::UDIVREM, ValueType, Expand);
		setOperationAction(ISD::SDIVREM, ValueType, Expand);
	}
	setOperationAction(ISD::LOAD, MVT::i64, Custom);
	setOperationAction(ISD::STORE, MVT::i64, Custom);
	setOperationAction(ISD::CTLZ, MVT::i16, Custom);
	setOperationAction(ISD::CTLZ, MVT::i40, Custom);
	setOperationAction(ISD::CTLZ_ZERO_UNDEF, MVT::i16, Custom);
	setOperationAction(ISD::CTLZ_ZERO_UNDEF, MVT::i40, Custom);
	setOperationAction(ISD::AND, MVT::i16, Custom);
	setOperationAction(ISD::AND, MVT::i40, Custom);
	setOperationAction(ISD::XOR, MVT::i16, Custom);
	setOperationAction(ISD::XOR, MVT::i40, Custom);
	setOperationAction(ISD::OR, MVT::i16, Custom);
	setOperationAction(ISD::OR, MVT::i40, Custom);
	setOperationAction(ISD::SHL, MVT::i16, Custom);
	setOperationAction(ISD::SHL, MVT::i40, Custom);
	setOperationAction(ISD::SRL, MVT::i16, Custom);
	setOperationAction(ISD::SRL, MVT::i40, Custom);
	setOperationAction(ISD::SRA, MVT::i16, Custom);
	setOperationAction(ISD::SRA, MVT::i40, Custom);
	setOperationAction(ISD::SHL_PARTS, MVT::i40, Expand);
	setOperationAction(ISD::SRL_PARTS, MVT::i40, Expand);
	setOperationAction(ISD::SRA_PARTS, MVT::i40, Expand);
	setLibcallName(RTLIB::SHL_I64, nullptr);
	setLibcallName(RTLIB::SRL_I64, nullptr);
	setLibcallName(RTLIB::SRA_I64, nullptr);

	setStackPointerRegisterToSaveRestore(Teak::SP);
	setOperationAction(ISD::DYNAMIC_STACKALLOC, MVT::i16, Custom);
	setOperationAction(ISD::STACKSAVE, MVT::Other, Custom);
	setOperationAction(ISD::STACKRESTORE, MVT::Other, Custom);
	setOperationAction(ISD::VASTART, MVT::Other, Custom);
	setOperationAction(ISD::VAARG, MVT::Other, Custom);
	setOperationAction(ISD::VACOPY, MVT::Other, Expand);
	setOperationAction(ISD::VAEND, MVT::Other, Expand);

	setSchedulingPreference(Sched::RegPressure);

	// Nodes that require custom lowering
	setOperationAction(ISD::GlobalAddress, MVT::i16, Custom);
	setOperationAction(ISD::GlobalAddress, MVT::i32, Custom);
	setOperationAction(ISD::GlobalAddress, MVT::i40, Custom);
	setOperationAction(ISD::ConstantPool, MVT::i16, Custom);
	setOperationAction(ISD::SIGN_EXTEND_INREG, MVT::i40, Expand);
	setOperationAction(ISD::SIGN_EXTEND_INREG, MVT::i32, Expand);
	setOperationAction(ISD::SIGN_EXTEND_INREG, MVT::i16, Expand);
	setOperationAction(ISD::SIGN_EXTEND_INREG, MVT::i8, Expand);
	setOperationAction(ISD::SIGN_EXTEND_INREG, MVT::i1, Expand);

	setOperationAction(ISD::Constant, MVT::i32, Promote);
	setOperationAction(ISD::Constant, MVT::i40, Custom);
	setOperationAction(ISD::Constant, MVT::i8, Promote);

	// setOperationAction(ISD::SIGN_EXTEND, MVT::i40, Expand);
	// setOperationAction(ISD::SIGN_EXTEND, MVT::i32, Promote);
	// setOperationAction(ISD::SIGN_EXTEND, MVT::i16, Promote);
	// setOperationAction(ISD::SIGN_EXTEND, MVT::i8, Promote);
	// setOperationAction(ISD::SIGN_EXTEND, MVT::i1, Promote);

	setOperationAction(ISD::SETCC, MVT::i40, Expand);
	setOperationAction(ISD::SETCC, MVT::i32, Expand);
	setOperationAction(ISD::SETCC, MVT::i16, Expand);
	setOperationAction(ISD::SETCC, MVT::i8, Expand);
	setOperationAction(ISD::SELECT, MVT::i40, Expand);
	setOperationAction(ISD::SELECT, MVT::i32, Expand);
	setOperationAction(ISD::SELECT, MVT::i16, Expand);
	setOperationAction(ISD::SELECT, MVT::i8, Expand);
	setOperationAction(ISD::SELECT_CC, MVT::i40, Custom);
	setOperationAction(ISD::SELECT_CC, MVT::i32, Custom);
	setOperationAction(ISD::SELECT_CC, MVT::i16, Custom);
	setOperationAction(ISD::SELECT_CC, MVT::i8, Custom);
	setOperationAction(ISD::BRCOND, MVT::Other, Expand);
	setOperationAction(ISD::BRIND, MVT::Other, Expand);
	setOperationAction(ISD::BR_JT, MVT::Other, Expand);
	setOperationAction(ISD::BR_CC, MVT::i8, Custom);
	setOperationAction(ISD::BR_CC, MVT::i16, Custom);
	setOperationAction(ISD::BR_CC, MVT::i32, Custom);
	setOperationAction(ISD::BR_CC, MVT::i40, Custom);

	//support for post increment and decrement
	setIndexedLoadAction(ISD::POST_INC, MVT::i16, Legal);
	setIndexedLoadAction(ISD::POST_DEC, MVT::i16, Legal);
	setIndexedStoreAction(ISD::POST_INC, MVT::i16, Legal);
	setIndexedStoreAction(ISD::POST_DEC, MVT::i16, Legal);

	// setOperationAction(ISD::STACKSAVE, MVT::Other, Expand);
	// setOperationAction(ISD::STACKSAVE, MVT::i40, Expand);
  	// setOperationAction(ISD::STACKRESTORE, MVT::Other, Expand);
  	// setOperationAction(ISD::STACKRESTORE, MVT::i40, Expand);

	//setOperationAction(ISD::SHL, MVT::i16, Promote);
	// setOperationAction(ISD::SIGN_EXTEND, MVT::i40, Expand);
	// setOperationAction(ISD::SIGN_EXTEND, MVT::i32, Expand);
	// setOperationAction(ISD::SIGN_EXTEND, MVT::i16, Expand);
	// setOperationAction(ISD::SIGN_EXTEND, MVT::i8, Expand);

	// setOperationAction(ISD::AND, MVT::i16, Promote);
	// setOperationAction(ISD::ADD, MVT::i16, Promote);
	// setOperationAction(ISD::Constant, MVT::i32, Promote);
	// setOperationAction(ISD::SIGN_EXTEND_INREG, MVT::i8,  Expand);
	// setOperationAction(ISD::TRUNCATE, MVT::i40, Expand);
	// setOperationAction(ISD::TRUNCATE, MVT::i32, Expand);
	// setOperationAction(ISD::TRUNCATE, MVT::i16, Expand);
	// setOperationAction(ISD::TRUNCATE, MVT::i8, Expand);
	// setOperationAction(ISD::TRUNCATE, MVT::i8,  Promote);
	// setOperationAction(ISD::SRA, MVT::i40, Custom);
	// setOperationAction(ISD::SRA, MVT::i32, Custom);
	// setOperationAction(ISD::SRA, MVT::i16, Custom);
	// setOperationAction(ISD::SRA, MVT::i8, Custom);
	// setOperationAction(ISD::TRUNCATE, MVT::i32, Promote);
	// setOperationAction(ISD::CopyToReg, MVT::i32,  Custom);
	// setOperationAction(ISD::CopyFromReg, MVT::i32,  Custom);
	// setOperationAction(ISD::CopyToReg, MVT::i40,  Expand);

	setLoadExtAction(ISD::EXTLOAD, MVT::i40, MVT::i32, Custom);
	setLoadExtAction(ISD::SEXTLOAD, MVT::i40, MVT::i32, Custom);
	setLoadExtAction(ISD::ZEXTLOAD, MVT::i40, MVT::i32, Custom);
	setTruncStoreAction(MVT::i40, MVT::i32, Custom);

	setLoadExtAction(ISD::EXTLOAD, MVT::i16, MVT::i1, Promote);
	setLoadExtAction(ISD::EXTLOAD, MVT::i40, MVT::i1, Promote);
	setLoadExtAction(ISD::EXTLOAD, MVT::i16, MVT::i8, Custom);
	setLoadExtAction(ISD::EXTLOAD, MVT::i40, MVT::i8, Custom);
	setLoadExtAction(ISD::ZEXTLOAD, MVT::i16, MVT::i1, Promote);
	setLoadExtAction(ISD::ZEXTLOAD, MVT::i40, MVT::i1, Promote);
	setLoadExtAction(ISD::ZEXTLOAD, MVT::i16, MVT::i8, Custom);
	setLoadExtAction(ISD::ZEXTLOAD, MVT::i40, MVT::i8, Custom);
	setLoadExtAction(ISD::SEXTLOAD, MVT::i16, MVT::i1, Promote);
	setLoadExtAction(ISD::SEXTLOAD, MVT::i40, MVT::i1, Promote);
	setLoadExtAction(ISD::SEXTLOAD, MVT::i16, MVT::i8, Custom);
	setLoadExtAction(ISD::SEXTLOAD, MVT::i40, MVT::i8, Custom);

	setTruncStoreAction(MVT::i40, MVT::i1, Expand);
	setTruncStoreAction(MVT::i32, MVT::i1, Expand);
	setTruncStoreAction(MVT::i16, MVT::i1, Expand);
	setTruncStoreAction(MVT::i8, MVT::i1, Expand);
	setTruncStoreAction(MVT::i40, MVT::i8, Custom);
	setTruncStoreAction(MVT::i32, MVT::i8, Expand);
	setTruncStoreAction(MVT::i16, MVT::i8, Custom);
}

// SDValue TeakTargetLowering::LowerSETCC(SDValue Op, SelectionDAG &DAG) const
// {
// 	SDValue LHS = Op.getOperand(0);
// 	SDValue RHS = Op.getOperand(1);
// 	ISD::CondCode CC = cast<CondCodeSDNode>(Op.getOperand(2))->get();
// 	SDLoc DL(Op);

// 	SDValue TargetCC;
// 	SDValue Cmp = getAVRCmp(LHS, RHS, CC, TargetCC, DAG, DL);

// 	SDValue TrueV = DAG.getConstant(1, DL, Op.getValueType());
// 	SDValue FalseV = DAG.getConstant(0, DL, Op.getValueType());
// 	SDVTList VTs = DAG.getVTList(Op.getValueType(), MVT::Glue);
// 	SDValue Ops[] = {TrueV, FalseV, TargetCC, Cmp};

// 	return DAG.getNode(AVRISD::SELECT_CC, DL, VTs, Ops);
// }

EVT TeakTargetLowering::getOptimalMemOpType(
    uint64_t Size, unsigned DstAlign, unsigned SrcAlign, bool IsMemset,
    bool ZeroMemset, bool MemcpyStrSrc, const AttributeList &FuncAttributes) const {
	// Prefer paired transfers for larger copies.
	return Size % 2 == 0 && (DstAlign == 0 || DstAlign >= 2) &&
		(IsMemset || SrcAlign == 0 || SrcAlign >= 2)
		? (Size >= 4 ? MVT::i32 : MVT::i16) : MVT::Other;
}

void TeakTargetLowering::computeKnownBitsForFrameIndex(
    SDValue FIOp, KnownBits &Known, const APInt &DemandedElts,
    const SelectionDAG &DAG, unsigned Depth) const {
	// Byte alignment cannot constrain word addresses.
}

bool TeakTargetLowering::isNarrowingProfitable(EVT VT1, EVT VT2) const
{
  	return VT2 != MVT::i8 && VT2 != MVT::i1;
}

bool TeakTargetLowering::getPostIndexedAddressParts(SDNode* N, SDNode* Op,
	SDValue &Base, SDValue &Offset, ISD::MemIndexedMode &AM, SelectionDAG &DAG) const 
{
	SDLoc DL(N);
	const LoadSDNode* ld = dyn_cast<LoadSDNode>(N);
	const StoreSDNode* st = dyn_cast<StoreSDNode>(N);
	if (!(ld && ld->getMemoryVT() == MVT::i16) && !(st && st->getMemoryVT() == MVT::i16))
		return false;
	if ((ld && ld->getValueType(0) != MVT::i16) ||
		(st && st->getValue().getValueType() != MVT::i16))
		return false;

	if (Op->getOpcode() != ISD::ADD && Op->getOpcode() != ISD::SUB)
		return false;	

	if (const ConstantSDNode* rhs = dyn_cast<ConstantSDNode>(Op->getOperand(1)))
	{
		int rhsc = rhs->getSExtValue();
		if (Op->getOpcode() == ISD::SUB)
			rhsc = -rhsc;
		if (rhsc != 1 && rhsc != -1)
			return false;

		Base = Op->getOperand(0);
		Offset = DAG.getConstant(rhsc, DL, MVT::i16);
		AM = ISD::POST_INC;

		return true;
	}
	// dbgs() << "getPostIndexedAddressParts\n";
	// EVT VT;
	// SDLoc DL(N);
	// Op->dump();
	// N->dump();
	return false;
}

bool TeakTargetLowering::allowsMemoryAccess(LLVMContext &Context, const DataLayout &DL, EVT VT, unsigned AddrSpace,
	unsigned Alignment, MachineMemOperand::Flags Flags, bool *Fast) const
{
	if (VT != MVT::i16 && VT != MVT::i32)
		return false;
	return TargetLowering::allowsMemoryAccess(Context, DL, VT, AddrSpace, Alignment, Flags, Fast);
}

bool TeakTargetLowering::allowsMisalignedMemoryAccesses(EVT VT, unsigned AddressSpace,
    unsigned Alignment, MachineMemOperand::Flags Flags, bool *Fast) const {
	// Pointers always address complete words.
	if (VT != MVT::i16)
		return false;
	if (Fast)
		*Fast = true;
	return true;
}

bool TeakTargetLowering::shouldReduceLoadWidth(SDNode* Load, ISD::LoadExtType ExtTy, EVT NewVT) const
{
	// Narrowing computes byte-addressed subword offsets.
	return false;
}


bool TeakTargetLowering::isLegalICmpImmediate(int64_t Imm) const
{
	return Imm >= -32768 && Imm <= 32767;
}

bool TeakTargetLowering::isLegalAddImmediate(int64_t Imm) const
{
	return Imm >= -32768 && Imm <= 32767;
}

bool TeakTargetLowering::isTruncateFree(Type *SrcTy, Type *DstTy) const
{
	if (!SrcTy->isIntegerTy() || !DstTy->isIntegerTy())
		return false;
	unsigned SrcBits = SrcTy->getPrimitiveSizeInBits();
	unsigned DestBits = DstTy->getPrimitiveSizeInBits();
	return (SrcBits == 40 && DestBits == 16);
}

bool TeakTargetLowering::isTruncateFree(EVT SrcVT, EVT DstVT) const
{
	if (SrcVT.isVector() || DstVT.isVector() || !SrcVT.isInteger() || !DstVT.isInteger())
		return false;
	unsigned SrcBits = SrcVT.getSizeInBits();
	unsigned DestBits = DstVT.getSizeInBits();
	return (SrcBits == 40 && DestBits == 16);
}

// Look at LHS/RHS/CC and see if they are a lowered setcc instruction.  If so
// set LHS/RHS and SPCC to the LHS/RHS of the setcc and SPCC to the condition.
static void lookThroughSetCC(SDValue &LHS, SDValue &RHS, ISD::CondCode CC, unsigned &SPCC)
{
	if (isNullConstant(RHS) && CC == ISD::SETNE && LHS.getOpcode() == TeakISD::SELECT_ICC &&
		LHS.getOperand(3).getOpcode() == TeakISD::CMPICC &&	isOneConstant(LHS.getOperand(0)) &&
		isNullConstant(LHS.getOperand(1)))
	{
		SDValue CMPCC = LHS.getOperand(3);
		SPCC = cast<ConstantSDNode>(LHS.getOperand(2))->getZExtValue();
		LHS = CMPCC.getOperand(0);
		RHS = CMPCC.getOperand(1);
	}
}

static TeakCC::CondCodes IntCondCCodeToICC(ISD::CondCode CC)
{
	switch (CC)
	{
		default: llvm_unreachable("Unknown integer condition code!");
		case ISD::SETEQ:  return TeakCC::Eq;
		case ISD::SETNE:  return TeakCC::Neq;
		case ISD::SETLT:  return TeakCC::Lt;
		case ISD::SETGT:  return TeakCC::Gt;
		case ISD::SETLE:  return TeakCC::Le;
		case ISD::SETGE:  return TeakCC::Ge;
		case ISD::SETULT: return TeakCC::Lt;
		case ISD::SETULE: return TeakCC::Le;
		case ISD::SETUGT: return TeakCC::Gt;
		case ISD::SETUGE: return TeakCC::Ge;
	}
}

static SDValue lowerWideComparison(SDValue Left, SDValue Right, ISD::CondCode Condition,
    const SDLoc &Location, SelectionDAG &DAG) {
	if (Left.getValueType() != MVT::i40 || Condition == ISD::SETEQ || Condition == ISD::SETNE)
		return SDValue();
	bool Unsigned = ISD::isUnsignedIntSetCC(Condition);
	if (Unsigned ? (DAG.SignBitIsZero(Left) && DAG.SignBitIsZero(Right))
		: (isNullConstant(Right) || (DAG.ComputeNumSignBits(Left) >= 2 &&
			DAG.ComputeNumSignBits(Right) >= 2)))
		return SDValue();
	SDValue Shift = DAG.getConstant(32, Location, MVT::i40);
	SDValue Mask = DAG.getConstant(UINT64_C(0xffffffff), Location, MVT::i40);
	SDValue LeftHigh = DAG.getNode(Unsigned ? ISD::SRL : ISD::SRA, Location, MVT::i40, Left, Shift);
	SDValue RightHigh = DAG.getNode(Unsigned ? ISD::SRL : ISD::SRA, Location, MVT::i40, Right, Shift);
	SDValue LeftLow = DAG.getNode(ISD::AND, Location, MVT::i40, Left, Mask);
	SDValue RightLow = DAG.getNode(ISD::AND, Location, MVT::i40, Right, Mask);
	ISD::CondCode LowCondition = Condition;
	if (LowCondition == ISD::SETLT) LowCondition = ISD::SETULT;
	if (LowCondition == ISD::SETLE) LowCondition = ISD::SETULE;
	if (LowCondition == ISD::SETGT) LowCondition = ISD::SETUGT;
	if (LowCondition == ISD::SETGE) LowCondition = ISD::SETUGE;
	auto Compare = [&](SDValue First, SDValue Second, ISD::CondCode Code) {
		SDValue Flag = DAG.getNode(Code == ISD::SETEQ ? TeakISD::CMPZICC : TeakISD::CMPICC,
			Location, MVT::Glue, First, Second);
		return DAG.getNode(TeakISD::SELECT_ICC, Location, MVT::i16,
			DAG.getConstant(1, Location, MVT::i16), DAG.getConstant(0, Location, MVT::i16),
			DAG.getConstant(IntCondCCodeToICC(Code), Location, MVT::i40), Flag);
	};
	SDValue EqualHigh = Compare(LeftHigh, RightHigh, ISD::SETEQ);
	SDValue CompareHigh = Compare(LeftHigh, RightHigh, Condition);
	SDValue CompareLow = Compare(LeftLow, RightLow, LowCondition);
	return DAG.getSelect(Location, MVT::i16, EqualHigh, CompareLow, CompareHigh);
}

SDValue TeakTargetLowering::LowerSELECT_CC(SDValue Op, SelectionDAG &DAG) const
{
	SDValue LHS = Op.getOperand(0);
	SDValue RHS = Op.getOperand(1);
	ISD::CondCode CC = cast<CondCodeSDNode>(Op.getOperand(4))->get();
	SDValue TrueVal = Op.getOperand(2);
	SDValue FalseVal = Op.getOperand(3);
	SDLoc dl(Op);
	unsigned Opc, SPCC = ~0U;

	// If this is a select_cc of a "setcc", and if the setcc got lowered into
	// an CMP[IF]CC/SELECT_[IF]CC pair, find the original compared values.
	lookThroughSetCC(LHS, RHS, CC, SPCC);
	if (SPCC == ~0U) {
		SDValue Comparison = lowerWideComparison(LHS, RHS, CC, dl, DAG);
		if (Comparison) {
			LHS = Comparison;
			RHS = DAG.getConstant(0, dl, MVT::i16);
			CC = ISD::SETNE;
		}
	}

	bool unsgn = false;
	if(CC == ISD::SETULT || CC == ISD::SETULE || CC == ISD::SETUGT || CC == ISD::SETUGE)
		unsgn = true;

	if(LHS.getValueType() != MVT::i40)
		LHS = DAG.getNode(unsgn ? ISD::ZERO_EXTEND : ISD::SIGN_EXTEND, dl, MVT::i40, LHS);

	if(RHS.getValueType() != MVT::i40)
		RHS = DAG.getNode(unsgn ? ISD::ZERO_EXTEND : ISD::SIGN_EXTEND, dl, MVT::i40, RHS);

	SDValue CompareFlag;
	if (LHS.getValueType().isInteger())
	{
		Opc = TeakISD::SELECT_ICC;
		if (SPCC == ~0U)
			SPCC = IntCondCCodeToICC(CC);
		CompareFlag = DAG.getNode((SPCC == TeakCC::Eq || SPCC == TeakCC::Neq) ? TeakISD::CMPZICC : TeakISD::CMPICC, dl, MVT::Glue, LHS, RHS);
	}
	else
		llvm_unreachable("!LHS.getValueType().isInteger()");
	return DAG.getNode(Opc, dl, TrueVal.getValueType(), TrueVal, FalseVal,
						DAG.getConstant(SPCC, dl, MVT::i40), CompareFlag);
}

SDValue TeakTargetLowering::LowerBR_CC(SDValue Op, SelectionDAG &DAG) const
{
	SDValue Chain = Op.getOperand(0);
	ISD::CondCode CC = cast<CondCodeSDNode>(Op.getOperand(1))->get();
	SDValue LHS = Op.getOperand(2);
	SDValue RHS = Op.getOperand(3);
	SDValue Dest = Op.getOperand(4);
	SDLoc dl(Op);
	unsigned Opc, SPCC = ~0U;

	// If this is a br_cc of a "setcc", and if the setcc got lowered into
	// an CMP[IF]CC/SELECT_[IF]CC pair, find the original compared values.
	lookThroughSetCC(LHS, RHS, CC, SPCC);
	if (SPCC == ~0U) {
		SDValue Comparison = lowerWideComparison(LHS, RHS, CC, dl, DAG);
		if (Comparison) {
			LHS = Comparison;
			RHS = DAG.getConstant(0, dl, MVT::i16);
			CC = ISD::SETNE;
		}
	}

	bool unsgn = false;
	if(CC == ISD::SETULT || CC == ISD::SETULE || CC == ISD::SETUGT || CC == ISD::SETUGE)
		unsgn = true;

	if(LHS.getValueType() != MVT::i40)
		LHS = DAG.getNode(unsgn ? ISD::ZERO_EXTEND : ISD::SIGN_EXTEND, dl, MVT::i40, LHS);

	if(RHS.getValueType() != MVT::i40)
		RHS = DAG.getNode(unsgn ? ISD::ZERO_EXTEND : ISD::SIGN_EXTEND, dl, MVT::i40, RHS);

	// Get the condition flag.
	SDValue CompareFlag;
	if (LHS.getValueType().isInteger())
	{
		if (SPCC == ~0U)
			SPCC = IntCondCCodeToICC(CC);

		CompareFlag = DAG.getNode((SPCC == TeakCC::Eq || SPCC == TeakCC::Neq) ? TeakISD::CMPZICC : TeakISD::CMPICC, dl, MVT::Glue, LHS, RHS);
		Opc = TeakISD::BRICC;
	}
	else
		llvm_unreachable("!LHS.getValueType().isInteger()");
	return DAG.getNode(Opc, dl, MVT::Other, Chain, Dest,
						DAG.getConstant(SPCC, dl, MVT::i40), CompareFlag);
}

SDValue TeakTargetLowering::LowerOperation(SDValue Op, SelectionDAG &DAG) const
{
	// dbgs() << "LowerOperation\n";
	// sys::PrintStackTrace(dbgs());

	// DAG.dump();
	// Op.dump(&DAG);
	switch (Op.getOpcode()) 
	{
		case ISD::VASTART: {
			SDLoc Location(Op);
			MachineFunction &Function = DAG.getMachineFunction();
			int FrameIndex = Function.getInfo<TeakFunctionInfo>()->getVarArgsFrameIndex();
			SDValue Address = DAG.getFrameIndex(FrameIndex, MVT::i16);
			return DAG.getStore(Op.getOperand(0), Location, Address, Op.getOperand(1),
				MachinePointerInfo(cast<SrcValueSDNode>(Op.getOperand(2))->getValue()), 2);
		}
		case ISD::VAARG: {
			SDLoc Location(Op);
			EVT ValueType = Op.getValueType();
			assert((ValueType == MVT::i16 || ValueType == MVT::i40) && "Unsupported argument type");
			SDValue List = Op.getOperand(1);
			MachinePointerInfo ListInfo(cast<SrcValueSDNode>(Op.getOperand(2))->getValue());
			SDValue Address = DAG.getLoad(MVT::i16, Location, Op.getOperand(0), List, ListInfo, 2);
			SDValue Chain = Address.getValue(1);
			SDValue Value = DAG.getConstant(0, Location, ValueType);
			unsigned WordCount = ValueType == MVT::i16 ? 1 : 3;
			for (unsigned Index = 0; Index < WordCount; ++Index) {
				SDValue Word = DAG.getLoad(MVT::i16, Location, Chain,
					DAG.getMemBasePlusOffset(Address, Index, Location), MachinePointerInfo(), 2);
				Chain = Word.getValue(1);
				SDValue Part = DAG.getZExtOrTrunc(Word, Location, ValueType);
				Part = DAG.getNode(ISD::SHL, Location, ValueType, Part,
					DAG.getConstant((WordCount - Index - 1) * 16, Location, MVT::i40));
				Value = DAG.getNode(ISD::OR, Location, ValueType, Value, Part);
			}
			SDValue Next = DAG.getMemBasePlusOffset(Address, WordCount, Location);
			Chain = DAG.getStore(Chain, Location, Next, List, ListInfo, 2);
			return DAG.getMergeValues({Value, Chain}, Location);
		}
		case ISD::STACKSAVE:
			return DAG.getCopyFromReg(Op.getOperand(0), SDLoc(Op), Teak::SP, MVT::i16);
		case ISD::STACKRESTORE: {
			SDLoc Location(Op);
			SDValue Chain = DAG.getCopyToReg(Op.getOperand(0), Location, Teak::SP, Op.getOperand(1));
			return SDValue(DAG.getMachineNode(Teak::NOP, Location, MVT::Other, Chain), 0);
		}
		case ISD::DYNAMIC_STACKALLOC: {
			SDLoc Location(Op);
			SDValue Stack = DAG.getCopyFromReg(Op.getOperand(0), Location, Teak::SP, MVT::i16);
			SDValue Words = DAG.getNode(ISD::SRL, Location, MVT::i16, Op.getOperand(1),
				DAG.getConstant(1, Location, MVT::i16));
			SDValue Address = DAG.getNode(ISD::SUB, Location, MVT::i16, Stack, Words);
			unsigned Alignment = cast<ConstantSDNode>(Op.getOperand(2))->getZExtValue() / 2;
			if (Alignment > 1)
				Address = DAG.getNode(ISD::AND, Location, MVT::i16, Address,
					DAG.getConstant(APInt(16, ~(Alignment - 1)), Location, MVT::i16));
			SDValue Chain = DAG.getCopyToReg(Stack.getValue(1), Location, Teak::SP, Address);
			Chain = SDValue(DAG.getMachineNode(Teak::NOP, Location, MVT::Other, Chain), 0);
			return DAG.getMergeValues({Address, Chain}, Location);
		}
		case ISD::UDIV:
		case ISD::UREM:
		case ISD::SDIV:
		case ISD::SREM: {
			bool Signed = Op.getOpcode() == ISD::SDIV || Op.getOpcode() == ISD::SREM;
			bool Remainder = Op.getOpcode() == ISD::UREM || Op.getOpcode() == ISD::SREM;
			const char *Name = Signed ? (Remainder ? "__teak_srem40" : "__teak_sdiv40")
				: (Remainder ? "__teak_urem40" : "__teak_udiv40");
			SDLoc Location(Op);
			Type *ValueType = IntegerType::get(*DAG.getContext(), 40);
			ArgListTy Arguments;
			for (unsigned Index = 0; Index < 2; ++Index) {
				SDValue Value = Op.getOperand(Index);
				if (Value.getValueType() != MVT::i40)
					Value = DAG.getNode(Signed ? ISD::SIGN_EXTEND : ISD::ZERO_EXTEND,
						Location, MVT::i40, Value);
				ArgListEntry Argument;
				Argument.Node = Value;
				Argument.Ty = ValueType;
				Arguments.push_back(Argument);
			}
			CallLoweringInfo Call(DAG);
			Call.setDebugLoc(Location).setChain(DAG.getEntryNode())
				.setLibCallee(CallingConv::C, ValueType,
					DAG.getExternalSymbol(Name, MVT::i16), std::move(Arguments))
				.setIsPostTypeLegalization(true);
			SDValue Result = LowerCallTo(Call).first;
			return DAG.getZExtOrTrunc(Result, Location, Op.getValueType());
		}
		case ISD::ConstantPool: {
			ConstantPoolSDNode *Pool = cast<ConstantPoolSDNode>(Op);
			SDValue Address = DAG.getTargetConstantPool(Pool->getConstVal(), MVT::i16,
				Pool->getAlignment(), Pool->getOffset(), Pool->getTargetFlags());
			return DAG.getNode(TeakISD::WRAPPER, SDLoc(Op), MVT::i16, Address);
		}
		case ISD::LOAD: {
			LoadSDNode *Load = cast<LoadSDNode>(Op);
			if (Load->getMemoryVT() == MVT::i8) {
				assert(!Load->isAtomic() && !Load->isIndexed());
				SDLoc Location(Op);
				SDValue Word = DAG.getLoad(MVT::i16, Location, Load->getChain(), Load->getBasePtr(),
					Load->getPointerInfo(), Load->getAlignment(),
					Load->getMemOperand()->getFlags(), Load->getAAInfo());
				SDValue Value = DAG.getNode(ISD::AND, Location, MVT::i16, Word,
					DAG.getConstant(255, Location, MVT::i16));
				bool Signed = Load->getExtensionType() == ISD::SEXTLOAD;
				if (Signed)
					Value = DAG.getNode(ISD::SIGN_EXTEND_INREG, Location, MVT::i16, Value,
						DAG.getValueType(MVT::i8));
				if (Load->getValueType(0) == MVT::i40)
					Value = DAG.getNode(Signed ? ISD::SIGN_EXTEND : ISD::ZERO_EXTEND,
						Location, MVT::i40, Value);
				return DAG.getMergeValues({Value, Word.getValue(1)}, Location);
			}
			if (Load->getAlignment() >= 4 && Load->getExtensionType() != ISD::ZEXTLOAD)
				return SDValue();
			SDLoc Location(Op);
			SDValue High = DAG.getLoad(MVT::i16, Location, Load->getChain(), Load->getBasePtr(),
				Load->getPointerInfo(), Load->getAlignment(),
				Load->getMemOperand()->getFlags(), Load->getAAInfo());
			SDValue Low = DAG.getLoad(MVT::i16, Location, High.getValue(1),
				DAG.getMemBasePlusOffset(Load->getBasePtr(), 1, Location),
				Load->getPointerInfo().getWithOffset(2), MinAlign(Load->getAlignment(), 2),
				Load->getMemOperand()->getFlags(), Load->getAAInfo());
			SDValue Value = DAG.getNode(ISD::OR, Location, MVT::i40,
				DAG.getNode(ISD::SHL, Location, MVT::i40,
					DAG.getNode(ISD::ZERO_EXTEND, Location, MVT::i40, High),
					DAG.getConstant(16, Location, MVT::i40)),
				DAG.getNode(ISD::ZERO_EXTEND, Location, MVT::i40, Low));
			if (Load->getExtensionType() == ISD::SEXTLOAD)
				Value = DAG.getNode(ISD::SIGN_EXTEND_INREG, Location, MVT::i40, Value,
					DAG.getValueType(MVT::i32));
			return DAG.getMergeValues({Value, Low.getValue(1)}, Location);
		}
		case ISD::STORE: {
			StoreSDNode *Store = cast<StoreSDNode>(Op);
			SDLoc Location(Op);
			unsigned Width = Store->getMemoryVT().getSizeInBits();
			if (Width == 8) {
				assert(!Store->isAtomic() && !Store->isIndexed());
				SDValue Word = DAG.getZExtOrTrunc(Store->getValue(), Location, MVT::i16);
				Word = DAG.getNode(ISD::AND, Location, MVT::i16, Word,
					DAG.getConstant(255, Location, MVT::i16));
				return DAG.getStore(Store->getChain(), Location, Word, Store->getBasePtr(),
					Store->getPointerInfo(), Store->getAlignment(),
					Store->getMemOperand()->getFlags(), Store->getAAInfo());
			}
			if (Width == 32 && Store->getAlignment() >= 4)
				return SDValue();
			assert((Width == 32 || Width == 64) && !Store->isAtomic());
			SDValue Chain = Store->getChain();
			for (unsigned Index = 0; Index < Width / 16; ++Index) {
				SDValue Address = DAG.getMemBasePlusOffset(Store->getBasePtr(), Index, Location);
				SDValue Shift = DAG.getConstant(Width - 16 - 16 * Index, Location, MVT::i40);
				SDValue Word = DAG.getNode(ISD::TRUNCATE, Location, MVT::i16,
					DAG.getNode(ISD::SRL, Location, Store->getValue().getValueType(), Store->getValue(), Shift));
				Chain = DAG.getStore(Chain, Location, Word, Address,
					Store->getPointerInfo().getWithOffset(Index * 2),
					MinAlign(Store->getAlignment(), Index * 2),
					Store->getMemOperand()->getFlags(), Store->getAAInfo());
			}
			return Chain;
		}
		default:
			//Op.dump(&DAG);
			llvm_unreachable("Unimplemented operand");
	//case ISD::SELECT:        return LowerSELECT(Op, DAG);
		case ISD::SELECT_CC:
			return LowerSELECT_CC(Op, DAG); 
		case ISD::BR_CC:
			return LowerBR_CC(Op, DAG); 
		//case ISD::SETCC:
		//	return LowerSETCC(Op, DAG);
		case ISD::GlobalAddress:
			return LowerGlobalAddress(Op, DAG);
		case ISD::CTLZ:
		case ISD::CTLZ_ZERO_UNDEF:
		{
			// Use binary search for leading zeros.
			SDLoc Location(Op);
			EVT ValueType = Op.getValueType();
			unsigned Width = ValueType.getSizeInBits();
			SDValue Remaining = Op.getOperand(0);
			SDValue Zero = DAG.getConstant(0, Location, ValueType);
			SDValue HighestBit = Zero;
			unsigned Step = 1;
			while (Step * 2 < Width)
				Step *= 2;
			for (; Step; Step /= 2) {
				SDValue Distance = DAG.getConstant(Step, Location, MVT::i40);
				SDValue UpperBits = DAG.getNode(ISD::SRL, Location, ValueType, Remaining, Distance);
				SDValue Advanced = DAG.getNode(ISD::ADD, Location, ValueType, HighestBit,
					DAG.getConstant(Step, Location, ValueType));
				HighestBit = DAG.getSelectCC(Location, UpperBits, Zero, Advanced, HighestBit, ISD::SETNE);
				Remaining = DAG.getSelectCC(Location, UpperBits, Zero, UpperBits, Remaining, ISD::SETNE);
			}
			SDValue FinalBit = DAG.getSelectCC(Location, Remaining, Zero,
				DAG.getConstant(1, Location, ValueType), Zero, ISD::SETNE);
			SDValue BitCount = DAG.getNode(ISD::ADD, Location, ValueType, HighestBit, FinalBit);
			return DAG.getNode(ISD::SUB, Location, ValueType,
				DAG.getConstant(Width, Location, ValueType), BitCount);
		}
		case ISD::ADD:
		case ISD::SUB:
		{
			const SDNode *N = Op.getNode();
			SDLoc dl(N);
			assert(N->getValueType(0) == MVT::i16 && "Unexpected custom legalisation");
			if(isa<ConstantSDNode>(N->getOperand(1)))
				return DAG.getNode(Op.getOpcode(), dl, MVT::i16, N->getOperand(0), N->getOperand(1));
			SDValue NewOp0 = DAG.getNode(ISD::ANY_EXTEND, dl, MVT::i40, N->getOperand(0));
			SDValue NewOp1 = DAG.getNode(ISD::ANY_EXTEND, dl, MVT::i40, N->getOperand(1));
			SDValue NewWOp = DAG.getNode(Op.getOpcode(), dl, MVT::i40, NewOp0, NewOp1);
  			return DAG.getNode(ISD::TRUNCATE, dl, MVT::i16, NewWOp);
		}
		case ISD::AND:
		case ISD::OR:
		case ISD::XOR:
		{
			const SDNode *N = Op.getNode();
			SDLoc dl(N);
			TeakISD::NodeType nodeType;
			switch(Op.getOpcode())
			{
				case ISD::AND:
					nodeType = TeakISD::AND;
					break;
				case ISD::OR:
					nodeType = TeakISD::OR;
					break;
				case ISD::XOR:
					nodeType = TeakISD::XOR;
					break;
			}
			if(N->getValueType(0) == MVT::i40)
				return DAG.getNode(nodeType, dl, MVT::i40, N->getOperand(0), N->getOperand(1));
			assert(N->getValueType(0) == MVT::i16 && "Unexpected custom legalisation");
			if(isa<ConstantSDNode>(N->getOperand(1)))
				return DAG.getNode(nodeType, dl, MVT::i16, N->getOperand(0), N->getOperand(1));
			SDValue NewOp0 = DAG.getNode(ISD::ANY_EXTEND, dl, MVT::i40, N->getOperand(0));
			SDValue NewOp1 = DAG.getNode(ISD::ANY_EXTEND, dl, MVT::i40, N->getOperand(1));
			SDValue NewWOp = DAG.getNode(nodeType, dl, MVT::i40, NewOp0, NewOp1);
  			return DAG.getNode(ISD::TRUNCATE, dl, MVT::i16, NewWOp);
		}
		case ISD::Constant:
		{
			const APInt &Value = cast<ConstantSDNode>(Op)->getAPIntValue();
			if (Value.isIntN(32) || Value.isSignedIntN(32))
				return Op;
			SDLoc Location(Op);
			SDValue Upper = DAG.getConstant(Value.lshr(16), Location, MVT::i40);
			SDValue Lower = DAG.getConstant(Value.getZExtValue() & 65535, Location, MVT::i40);
			SDValue Shifted = DAG.getNode(TeakISD::SHIFT_ARITH, Location, MVT::i40,
				Upper, DAG.getConstant(16, Location, MVT::i16));
			return DAG.getNode(TeakISD::OR, Location, MVT::i40, Shifted, Lower);
		}
		case ISD::MULHU:
		case ISD::MULHS:
		{
			SDLoc Location(Op);
			SDValue LeftOperand = Op.getOperand(0);
			SDValue RightOperand = Op.getOperand(1);
			SDValue LeftDigits[4], RightDigits[4];
			SDValue Mask = DAG.getConstant(1023, Location, MVT::i40);
			SDValue DigitWidth = DAG.getConstant(10, Location, MVT::i40);
			for (unsigned Index = 0; Index < 4; ++Index) {
				SDValue Shift = DAG.getConstant(Index * 10, Location, MVT::i40);
				LeftDigits[Index] = DAG.getNode(ISD::TRUNCATE, Location, MVT::i16,
					DAG.getNode(ISD::AND, Location, MVT::i40,
						DAG.getNode(ISD::SRL, Location, MVT::i40, LeftOperand, Shift), Mask));
				RightDigits[Index] = DAG.getNode(ISD::TRUNCATE, Location, MVT::i16,
					DAG.getNode(ISD::AND, Location, MVT::i40,
						DAG.getNode(ISD::SRL, Location, MVT::i40, RightOperand, Shift), Mask));
			}
			SDValue Carry = DAG.getConstant(0, Location, MVT::i40);
			SDValue Result = Carry;
			for (unsigned Column = 0; Column < 8; ++Column) {
				SDValue Partial = Carry;
				for (unsigned Index = 0; Index < 4; ++Index) {
					if (Column < Index || Column - Index >= 4)
						continue;
					Partial = DAG.getNode(ISD::ADD, Location, MVT::i40, Partial,
						DAG.getNode(TeakISD::MPY, Location, MVT::i40,
							LeftDigits[Index], RightDigits[Column - Index]));
				}
				Carry = DAG.getNode(ISD::SRL, Location, MVT::i40, Partial, DigitWidth);
				if (Column >= 4)
					Result = DAG.getNode(ISD::OR, Location, MVT::i40, Result,
						DAG.getNode(ISD::SHL, Location, MVT::i40,
							DAG.getNode(ISD::AND, Location, MVT::i40, Partial, Mask),
							DAG.getConstant((Column - 4) * 10, Location, MVT::i40)));
			}
			if (Op.getOpcode() == ISD::MULHS) {
				SDValue SignShift = DAG.getConstant(39, Location, MVT::i40);
				SDValue LeftSign = DAG.getNode(ISD::SRA, Location, MVT::i40, LeftOperand, SignShift);
				SDValue RightSign = DAG.getNode(ISD::SRA, Location, MVT::i40, RightOperand, SignShift);
				Result = DAG.getNode(ISD::SUB, Location, MVT::i40, Result,
					DAG.getNode(ISD::AND, Location, MVT::i40, LeftSign, RightOperand));
				Result = DAG.getNode(ISD::SUB, Location, MVT::i40, Result,
					DAG.getNode(ISD::AND, Location, MVT::i40, RightSign, LeftOperand));
			}
			return Result;
		}
		case ISD::MUL:
		{
			const SDNode *N = Op.getNode();
			SDLoc dl(N);
			if (N->getValueType(0) == MVT::i40) {
				SDValue LeftOperand = N->getOperand(0);
				SDValue RightOperand = N->getOperand(1);
				bool LeftIsSignedWord = DAG.ComputeNumSignBits(LeftOperand) >= 25;
				bool RightIsSignedWord = DAG.ComputeNumSignBits(RightOperand) >= 25;
				auto NativeProduct = [&](SDValue Left, SDValue Right) {
					return DAG.getNode(TeakISD::MPY, dl, MVT::i40,
						DAG.getNode(ISD::TRUNCATE, dl, MVT::i16, Left),
						DAG.getNode(ISD::TRUNCATE, dl, MVT::i16, Right));
				};
				if (LeftIsSignedWord && RightIsSignedWord)
					return NativeProduct(LeftOperand, RightOperand);
				APInt UpperBits = APInt::getHighBitsSet(40, 24);
				if ((LeftIsSignedWord && DAG.MaskedValueIsZero(RightOperand, UpperBits)) ||
					(RightIsSignedWord && DAG.MaskedValueIsZero(LeftOperand, UpperBits))) {
					SDValue SignedWord = LeftIsSignedWord ? LeftOperand : RightOperand;
					SDValue UnsignedWord = LeftIsSignedWord ? RightOperand : LeftOperand;
					SDValue LowWord = DAG.getNode(ISD::AND, dl, MVT::i40, UnsignedWord,
						DAG.getConstant(0x7fff, dl, MVT::i40));
					SDValue HighBit = DAG.getNode(ISD::SRL, dl, MVT::i40, UnsignedWord,
						DAG.getConstant(15, dl, MVT::i40));
					return DAG.getNode(ISD::ADD, dl, MVT::i40,
						NativeProduct(SignedWord, LowWord),
						DAG.getNode(ISD::SHL, dl, MVT::i40, NativeProduct(SignedWord, HighBit),
							DAG.getConstant(15, dl, MVT::i40)));
				}
				if (LeftIsSignedWord || RightIsSignedWord) {
					SDValue SignedWord = LeftIsSignedWord ? LeftOperand : RightOperand;
					SDValue WideOperand = LeftIsSignedWord ? RightOperand : LeftOperand;
					SDValue Result = DAG.getConstant(0, dl, MVT::i40);
					for (unsigned Index = 0; Index < 3; ++Index) {
						SDValue Shift = DAG.getConstant(Index * 15, dl, MVT::i40);
						SDValue Word = DAG.getNode(ISD::AND, dl, MVT::i40,
							DAG.getNode(ISD::SRL, dl, MVT::i40, WideOperand, Shift),
							DAG.getConstant(0x7fff, dl, MVT::i40));
						Result = DAG.getNode(ISD::ADD, dl, MVT::i40, Result,
							DAG.getNode(ISD::SHL, dl, MVT::i40, NativeProduct(SignedWord, Word), Shift));
					}
					return Result;
				}
				// Keep signed multiplier inputs positive.
				SDValue Left[3], Right[3];
				SDValue Mask = DAG.getConstant(0x7fff, dl, MVT::i40);
				for (unsigned Index = 0; Index < 3; ++Index) {
					SDValue Shift = DAG.getConstant(Index * 15, dl, MVT::i40);
					Left[Index] = DAG.getNode(ISD::TRUNCATE, dl, MVT::i16,
						DAG.getNode(ISD::AND, dl, MVT::i40,
							DAG.getNode(ISD::SRL, dl, MVT::i40, N->getOperand(0), Shift), Mask));
					Right[Index] = DAG.getNode(ISD::TRUNCATE, dl, MVT::i16,
						DAG.getNode(ISD::AND, dl, MVT::i40,
							DAG.getNode(ISD::SRL, dl, MVT::i40, N->getOperand(1), Shift), Mask));
				}
				SDValue Result = DAG.getConstant(0, dl, MVT::i40);
				for (unsigned Column = 0; Column < 3; ++Column) {
					SDValue Partial = DAG.getConstant(0, dl, MVT::i40);
					for (unsigned Index = 0; Index <= Column; ++Index)
						Partial = DAG.getNode(ISD::ADD, dl, MVT::i40, Partial,
							DAG.getNode(TeakISD::MPY, dl, MVT::i40, Left[Index], Right[Column - Index]));
					Result = DAG.getNode(ISD::ADD, dl, MVT::i40, Result,
						DAG.getNode(ISD::SHL, dl, MVT::i40, Partial,
							DAG.getConstant(Column * 15, dl, MVT::i40)));
				}
				return Result;
			}
			assert(N->getValueType(0) == MVT::i16 && "Unexpected custom legalisation");
			return DAG.getNode(ISD::TRUNCATE, dl, MVT::i16, DAG.getNode(TeakISD::MPY, dl, MVT::i40, N->getOperand(0), N->getOperand(1)));
		}
		case ISD::SHL:
		{
			const SDNode *N = Op.getNode();
		 	SDLoc dl(N);
			if(N->getValueType(0) == MVT::i16)
			{
				return 
					DAG.getNode(ISD::TRUNCATE, dl, MVT::i16, 
						DAG.getNode(TeakISD::SHIFT_ARITH, dl, MVT::i40, 
							DAG.getNode(ISD::ZERO_EXTEND, dl, MVT::i40,
								N->getOperand(0)), 
							DAG.getNode(ISD::TRUNCATE, dl, MVT::i16, N->getOperand(1))));
			}
			else if(N->getValueType(0) == MVT::i40)
			{
				//emit arithmetic shift, because it is the same as logical for left
				//shifts, and we don't want to modify the shift flag if not needed
				return DAG.getNode(TeakISD::SHIFT_ARITH, dl, MVT::i40, 
					N->getOperand(0), 
					DAG.getNode(ISD::TRUNCATE, dl, MVT::i16, N->getOperand(1)));
			}
			else
				llvm_unreachable("Unimplemented shift operand");
		}
		case ISD::SRL:
		{
			const SDNode* N = Op.getNode();
		 	SDLoc dl(N);
			SDValue shiftOp = N->getOperand(1);
			if(N->getValueType(0) == MVT::i16)
			{
				return
					DAG.getNode(ISD::TRUNCATE, dl, MVT::i16, 
						DAG.getNode(TeakISD::SHIFT_LOGIC, dl, MVT::i40, 
							DAG.getNode(ISD::ZERO_EXTEND, dl, MVT::i40,
								N->getOperand(0)), 
							//negation for right shift
							DAG.getNode(ISD::TRUNCATE, dl, MVT::i16, 
								DAG.getNode(ISD::SUB, dl, MVT::i40,
									DAG.getConstant(0, dl, MVT::i40), N->getOperand(1)))));
			}
			else if(N->getValueType(0) == MVT::i40)
				return
					DAG.getNode(TeakISD::SHIFT_LOGIC, dl, MVT::i40,
						N->getOperand(0), 
						//negation for right shift
						DAG.getNode(ISD::TRUNCATE, dl, MVT::i16,
							DAG.getNode(ISD::SUB, dl, MVT::i40,
								DAG.getConstant(0, dl, MVT::i40), N->getOperand(1))));
			else
				llvm_unreachable("Unimplemented shift operand");
		}
		case ISD::SRA:
		{
			const SDNode *N = Op.getNode();
		 	SDLoc dl(N);
			if(N->getValueType(0) == MVT::i16)
			{
				return
					DAG.getNode(ISD::TRUNCATE, dl, MVT::i16, 
						DAG.getNode(TeakISD::SHIFT_ARITH, dl, MVT::i40, 
							DAG.getNode(ISD::SIGN_EXTEND, dl, MVT::i40,
								N->getOperand(0)), 
							//negation for right shift
							DAG.getNode(ISD::TRUNCATE, dl, MVT::i16, 
								DAG.getNode(ISD::SUB, dl, MVT::i40,
									DAG.getConstant(0, dl, MVT::i40), N->getOperand(1)))));
			}
			else if(N->getValueType(0) == MVT::i40)
				return
					DAG.getNode(TeakISD::SHIFT_ARITH, dl, MVT::i40,
						N->getOperand(0), 
						//negation for right shift
						DAG.getNode(ISD::TRUNCATE, dl, MVT::i16, 
							DAG.getNode(ISD::SUB, dl, MVT::i40,
								DAG.getConstant(0, dl, MVT::i40), N->getOperand(1))));
			else
				llvm_unreachable("Unimplemented shift operand");
		}
		// case ISD::SHL:
		// case ISD::SRL:
		// case ISD::SRA:
		// {
		// 	DAG.dump();
		// 	const SDNode *N = Op.getNode();
		// 	SDLoc dl(N);
		// 	assert(N->getValueType(0) == MVT::i16 && "Unexpected custom legalisation");
		// 	SDValue NewOp0 = DAG.getNode(Op.getOpcode() == ISD::SRA ? ISD::SIGN_EXTEND : ISD::ZERO_EXTEND, dl, MVT::i40, N->getOperand(0));
		// 	SDValue NewWOp = DAG.getNode(N->getOpcode(), dl, MVT::i40, NewOp0, N->getOperand(1));
		// 	//SDValue NewRes = DAG.getNode(ISD::SIGN_EXTEND_INREG, dl, MVT::i40, NewWOp, DAG.getValueType(MVT::i16));
  		// 	return DAG.getNode(ISD::TRUNCATE, dl, MVT::i16, NewWOp);//NewRes);
		// }
		// case ISD::MUL:
		// {
		// 	const SDNode *N = Op.getNode();
		// 	SDLoc dl(N);
		// 	assert(N->getValueType(0) == MVT::i16 && "Unexpected custom legalisation");
		// 	//SDValue NewOp0 = DAG.getNode(ISD::SIGN_EXTEND, dl, MVT::i32, N->getOperand(0));
		// 	//SDValue NewOp1 = DAG.getNode(ISD::SIGN_EXTEND, dl, MVT::i32, N->getOperand(1));
		// 	SDValue NewWOp = DAG.getNode(Teak::MOV_p0_regnob16, dl, MVT::i16, DAG.getNode(Teak::MPY_y0_regnob16, dl, MVT::i32, N->getOperand(0), N->getOperand(1)));
		// 	//SDValue NewRes = DAG.getNode(ISD::SIGN_EXTEND_INREG, dl, MVT::i40, NewWOp, DAG.getValueType(MVT::i16));
  		// 	return NewWOp;//DAG.getNode(ISD::TRUNCATE, dl, MVT::i16, NewWOp);//NewRes);
		// }
		// case ISD::SRA:
		// {
		//   const SDNode *N = Op.getNode();
		//    SDLoc dl(N);
		//   return DAG.getNode(Teak::SHFI_ab_ab, dl, MVT::i40, Op->getOperand(0),
		//   Op->getOperand(1));
		// }
		// case ISD::CopyToReg:
		// {
		//   dbgs() << "LowerOperation = ISD::CopyToReg\n";
		//   const SDNode *N = Op.getNode();
		//   SDLoc dl(N);
		//   return DAG.getNode(ISD::ZERO_EXTEND, dl, MVT::i40,
		//   Op->getOperand(1));//DAG.getCopyToReg(Op.getCha, dl, Op->getOperand(0),
		//   DAG.getNode(ISD::ZERO_EXTEND, dl, MVT::i40, Op->getOperand(1)),
		//   Op->getOperand(2));
		// }
		// case ISD::CopyFromReg:
		// {
		//   dbgs() << "LowerOperation = ISD::CopyFromReg\n";
		//   const SDNode *N = Op.getNode();
		//   SDLoc dl(N);
		//   return DAG.getNode(ISD::ZERO_EXTEND, dl, MVT::i40,
		//   Op);//DAG.getCopyToReg(Op.getCha, dl, Op->getOperand(0),
		//   DAG.getNode(ISD::ZERO_EXTEND, dl, MVT::i40, Op->getOperand(1)),
		//   Op->getOperand(2));
		// }
	}
	return SDValue();
}

SDValue TeakTargetLowering::LowerGlobalAddress(SDValue Op, SelectionDAG &DAG) const
{
	EVT VT = Op.getValueType();
	GlobalAddressSDNode *GlobalAddr = cast<GlobalAddressSDNode>(Op.getNode());
	int64_t Offset = cast<GlobalAddressSDNode>(Op)->getOffset();
	if (GlobalAddr->getGlobal()->getAddressSpace() == 1) {
		assert(Offset == 0 && "Unexpected program symbol offset");
		SDLoc Location(Op);
		Constant *Address = ConstantExpr::getPtrToInt(
			const_cast<GlobalValue *>(GlobalAddr->getGlobal()),
			Type::getInt32Ty(*DAG.getContext()));
		SDValue Pool = DAG.getConstantPool(Address, MVT::i16, 4);
		MachinePointerInfo PointerInfo = MachinePointerInfo::getConstantPool(DAG.getMachineFunction());
		SDValue High = DAG.getLoad(MVT::i16, Location, DAG.getEntryNode(), Pool, PointerInfo, 4);
		SDValue Low = DAG.getLoad(MVT::i16, Location, High.getValue(1),
			DAG.getMemBasePlusOffset(Pool, 1, Location), PointerInfo.getWithOffset(2), 2);
		return DAG.getNode(ISD::OR, Location, MVT::i40,
			DAG.getNode(ISD::SHL, Location, MVT::i40,
				DAG.getNode(ISD::ZERO_EXTEND, Location, MVT::i40, High),
				DAG.getConstant(16, Location, MVT::i40)),
			DAG.getNode(ISD::ZERO_EXTEND, Location, MVT::i40, Low));
	}
	if(VT == MVT::i16)
		return DAG.getNode(TeakISD::WRAPPER, SDLoc(Op), MVT::i16, DAG.getTargetGlobalAddress(GlobalAddr->getGlobal(), Op, MVT::i16, Offset));
	else
		return DAG.getNode(TeakISD::WRAPPER, SDLoc(Op), MVT::i40, DAG.getTargetGlobalAddress(GlobalAddr->getGlobal(), Op, MVT::i40, Offset));
}

//===----------------------------------------------------------------------===//
//                      Calling Convention Implementation
//===----------------------------------------------------------------------===//

#include "TeakGenCallingConv.inc"

//===----------------------------------------------------------------------===//
//                  Call Calling Convention Implementation
//===----------------------------------------------------------------------===//

/// Teak call implementation
SDValue TeakTargetLowering::LowerCall(TargetLowering::CallLoweringInfo &CLI,
									  SmallVectorImpl<SDValue> &InVals) const {
  SelectionDAG &DAG = CLI.DAG;
  SDLoc &Loc = CLI.DL;
  SmallVectorImpl<ISD::OutputArg> &Outs = CLI.Outs;
  SmallVectorImpl<SDValue> &OutVals = CLI.OutVals;
  SmallVectorImpl<ISD::InputArg> &Ins = CLI.Ins;
  SDValue Chain = CLI.Chain;
  SDValue Callee = CLI.Callee;
  CallingConv::ID CallConv = CLI.CallConv;
  const bool isVarArg = CLI.IsVarArg;

  CLI.IsTailCall = false;

  // Analyze operands of the call, assigning locations to each operand.
  SmallVector<CCValAssign, 16> ArgLocs;
  CCState CCInfo(CallConv, isVarArg, DAG.getMachineFunction(), ArgLocs,
				 *DAG.getContext());
  CCInfo.AnalyzeCallOperands(Outs, CC_Teak);

  // Get the size of the outgoing arguments stack space requirement.
  const unsigned NumBytes = CCInfo.getNextStackOffset();

  Chain = DAG.getCALLSEQ_START(Chain, NumBytes, 0, Loc);

  SmallVector<std::pair<unsigned, SDValue>, 8> RegsToPass;
  SmallVector<SDValue, 8> MemOpChains;

  if (!isa<GlobalAddressSDNode>(Callee) && !isa<ExternalSymbolSDNode>(Callee)) {
    SDValue Address = DAG.getZExtOrTrunc(Callee, Loc, MVT::i40);
    RegsToPass.emplace_back(Teak::R0,
        DAG.getNode(ISD::TRUNCATE, Loc, MVT::i16, Address));
    RegsToPass.emplace_back(Teak::R1,
        DAG.getNode(ISD::TRUNCATE, Loc, MVT::i16,
            DAG.getNode(ISD::SRL, Loc, MVT::i40, Address,
                DAG.getConstant(16, Loc, MVT::i40))));
    Callee = DAG.getTargetExternalSymbol("__teak_indirect_call", MVT::i40);
  }

  // Walk the register/memloc assignments, inserting copies/loads.
  for (unsigned i = 0, e = ArgLocs.size(); i != e; ++i) {
	CCValAssign &VA = ArgLocs[i];
	SDValue Arg = OutVals[i];

	// We only handle fully promoted arguments.
	//dbgs() << VA.getLocInfo() << "\n";
	//assert(VA.getLocInfo() == CCValAssign::Full && "Unhandled loc info");

	// Promote the value if needed. With Clang this should not happen.
    switch (VA.getLocInfo()) {
		default:
			llvm_unreachable("Unknown loc info!");
		case CCValAssign::Full:
			break;
		case CCValAssign::SExt:
			Arg = DAG.getNode(ISD::SIGN_EXTEND, Loc, VA.getLocVT(), Arg);
			break;
		case CCValAssign::ZExt:
			Arg = DAG.getNode(ISD::ZERO_EXTEND, Loc, VA.getLocVT(), Arg);
			break;
		case CCValAssign::AExt:
			Arg = DAG.getNode(ISD::ANY_EXTEND, Loc, VA.getLocVT(), Arg);
			break;
		case CCValAssign::BCvt:
			Arg = DAG.getNode(ISD::BITCAST, Loc, VA.getLocVT(), Arg);
			break;
    }

	if (VA.isRegLoc()) {
	  RegsToPass.push_back(std::make_pair(VA.getLocReg(), Arg));
	  continue;
	}

	assert(VA.isMemLoc() &&
		   "Only support passing arguments through registers or via the stack");

	SDValue StackPointer = DAG.getCopyFromReg(Chain, Loc, Teak::SP, MVT::i16);
	SDValue StoreChain = StackPointer.getValue(1);
	unsigned WordCount = VA.getLocVT() == MVT::i16 ? 1 : 3;
	for (unsigned WordIndex = 0; WordIndex < WordCount; ++WordIndex) {
		SDValue Address = DAG.getNode(ISD::ADD, Loc, MVT::i16, StackPointer,
			DAG.getConstant(VA.getLocMemOffset() / 2 + WordIndex, Loc, MVT::i16));
		SDValue Word = Arg;
		if (WordCount > 1)
			Word = DAG.getNode(ISD::TRUNCATE, Loc, MVT::i16,
				DAG.getNode(ISD::SRL, Loc, MVT::i40, Arg,
					DAG.getConstant((WordCount - WordIndex - 1) * 16, Loc, MVT::i40)));
		StoreChain = DAG.getStore(StoreChain, Loc, Word, Address, MachinePointerInfo(), 2);
	}
	MemOpChains.push_back(StoreChain);
  }

  // Emit all stores, make sure they occur before the call.
  if (!MemOpChains.empty()) {
	Chain = DAG.getNode(ISD::TokenFactor, Loc, MVT::Other, MemOpChains);
  }

  // Build a sequence of copy-to-reg nodes chained together with token chain
  // and flag operands which copy the outgoing args into the appropriate regs.
  SDValue InFlag;
  for (auto &Reg : RegsToPass)
  {
	Chain = DAG.getCopyToReg(Chain, Loc, Reg.first, Reg.second, InFlag);
	InFlag = Chain.getValue(1);
  }

  // We only support calling global addresses.
  //GlobalAddressSDNode *G = dyn_cast<GlobalAddressSDNode>(Callee);
  //assert(G && "We only support the calling of global addresses");

  //EVT PtrVT = getPointerTy(DAG.getDataLayout());
  //Callee = DAG.getGlobalAddress(G->getGlobal(), Loc, PtrVT, 0);
  if (const GlobalAddressSDNode *G = dyn_cast<GlobalAddressSDNode>(Callee))
  {
    	const GlobalValue *GV = G->getGlobal();
    	Callee = DAG.getTargetGlobalAddress(GV, Loc, MVT::i40);
  } 
  else if (const ExternalSymbolSDNode *ES = dyn_cast<ExternalSymbolSDNode>(Callee))
    	Callee = DAG.getTargetExternalSymbol(ES->getSymbol(), MVT::i40);

  std::vector<SDValue> Ops;
  Ops.push_back(Chain);
  Ops.push_back(Callee);

  // Add argument registers to the end of the list so that they are known live
  // into the call.
  for (auto &Reg : RegsToPass) {
	Ops.push_back(DAG.getRegister(Reg.first, Reg.second.getValueType()));
  }

  // Add a register mask operand representing the call-preserved registers.
  const uint32_t *Mask;
  const TargetRegisterInfo *TRI = DAG.getSubtarget().getRegisterInfo();
  Mask = TRI->getCallPreservedMask(DAG.getMachineFunction(), CallConv);

  assert(Mask && "Missing call preserved mask for calling convention");
  Ops.push_back(DAG.getRegisterMask(Mask));

  if (InFlag.getNode()) {
	Ops.push_back(InFlag);
  }

  SDVTList NodeTys = DAG.getVTList(MVT::Other, MVT::Glue);

  // Returns a chain and a flag for retval copy to use.
  Chain = DAG.getNode(TeakISD::CALL, Loc, NodeTys, Ops);
  InFlag = Chain.getValue(1);

  Chain = DAG.getCALLSEQ_END(Chain, DAG.getIntPtrConstant(NumBytes, Loc, true),
							 DAG.getIntPtrConstant(0, Loc, true), InFlag, Loc);
  if (!Ins.empty()) {
	InFlag = Chain.getValue(1);
  }

  // Handle result values, copying them out of physregs into vregs that we
  // return.
  return LowerCallResult(Chain, InFlag, CallConv, isVarArg, Ins, Loc, DAG,
						 InVals);
}

SDValue TeakTargetLowering::LowerCallResult(
	SDValue Chain, SDValue InGlue, CallingConv::ID CallConv, bool isVarArg,
	const SmallVectorImpl<ISD::InputArg> &Ins, const SDLoc &dl,
	SelectionDAG &DAG, SmallVectorImpl<SDValue> &InVals) const {
  // Assign locations to each value returned by this call.
  SmallVector<CCValAssign, 16> RVLocs;
  CCState CCInfo(CallConv, isVarArg, DAG.getMachineFunction(), RVLocs,
				 *DAG.getContext());

  CCInfo.AnalyzeCallResult(Ins, RetCC_Teak);

  // Copy all of the result registers out of their specified physreg.
  for (auto &Loc : RVLocs) {
	SDValue RV =
		DAG.getCopyFromReg(Chain, dl, Loc.getLocReg(), Loc.getValVT(), InGlue);
	Chain = RV.getValue(1);
	InGlue = Chain.getValue(2);

	// if (Loc.isExtInLoc())
	//   RV = DAG.getNode(ISD::TRUNCATE, dl, Loc.getValVT(), RV);
	InVals.push_back(RV);
  }

  return Chain;
}

//===----------------------------------------------------------------------===//
//             Formal Arguments Calling Convention Implementation
//===----------------------------------------------------------------------===//

/// Teak formal arguments implementation
SDValue TeakTargetLowering::LowerFormalArguments(
	SDValue Chain, CallingConv::ID CallConv, bool isVarArg,
	const SmallVectorImpl<ISD::InputArg> &Ins, const SDLoc &dl,
	SelectionDAG &DAG, SmallVectorImpl<SDValue> &InVals) const {
  MachineFunction &MF = DAG.getMachineFunction();
  MachineRegisterInfo &RegInfo = MF.getRegInfo();

  // Assign locations to all of the incoming arguments.
  SmallVector<CCValAssign, 16> ArgLocs;
  CCState CCInfo(CallConv, isVarArg, DAG.getMachineFunction(), ArgLocs,
				 *DAG.getContext());

  CCInfo.AnalyzeFormalArguments(Ins, CC_Teak);

  if (isVarArg) {
	int FrameIndex = MF.getFrameInfo().CreateFixedObject(2, CCInfo.getNextStackOffset() + 4, true);
	MF.getInfo<TeakFunctionInfo>()->setVarArgsFrameIndex(FrameIndex);
  }

  for (auto &VA : ArgLocs) {
	if (VA.isRegLoc()) {
	  // Arguments passed in registers
	  EVT RegVT = VA.getLocVT();
	  const TargetRegisterClass *RC;

	  if (RegVT == MVT::i16)
		RC = &Teak::ABLRegsRegClass;
	  else if (RegVT == MVT::i40)
		RC = &Teak::ABRegsRegClass;
	  else
		llvm_unreachable("RegVT not supported by FORMAL_ARGUMENTS Lowering");

	  // assert((RegVT.getSimpleVT().SimpleTy == MVT::i16 ||
	  // RegVT.getSimpleVT().SimpleTy == MVT::i40) &&
	  //      "Only support MVT::i16 and MVT::i40 register passing");
	  dbgs() << "LowerFormalArguments: " << RegVT.getEVTString()
			 << " locreg=" << VA.getLocReg() << "\n";
	  unsigned VReg = MF.addLiveIn(VA.getLocReg(), RC);
	  SDValue ArgIn = DAG.getCopyFromReg(Chain, dl, VReg, RegVT);
	  // Truncate the register down to the argument type.
	  // if (VA.isExtInLoc())
	  //   ArgIn = DAG.getNode(ISD::TRUNCATE, dl, VA.getValVT(), ArgIn);

	  InVals.push_back(ArgIn);
	  continue;
	}

	assert(VA.isMemLoc() && "Expected a stack argument");
	unsigned WordCount = VA.getLocVT() == MVT::i16 ? 1 : 3;
	int FrameIndex = MF.getFrameInfo().CreateFixedObject(WordCount * 2,
		VA.getLocMemOffset() + 4, true);
	SDValue Base = DAG.getFrameIndex(FrameIndex, MVT::i16);
	SDValue Value = DAG.getConstant(0, dl, VA.getLocVT());
	for (unsigned WordIndex = 0; WordIndex < WordCount; ++WordIndex) {
		SDValue Address = DAG.getMemBasePlusOffset(Base, WordIndex, dl);
		SDValue Word = DAG.getLoad(MVT::i16, dl, Chain, Address,
			MachinePointerInfo::getFixedStack(MF, FrameIndex, WordIndex * 2), 2);
		Chain = Word.getValue(1);
		if (WordCount == 1) {
			Value = Word;
		} else {
			SDValue Part = DAG.getNode(ISD::ZERO_EXTEND, dl, MVT::i40, Word);
			Part = DAG.getNode(ISD::SHL, dl, MVT::i40, Part,
				DAG.getConstant((WordCount - WordIndex - 1) * 16, dl, MVT::i40));
			Value = DAG.getNode(ISD::OR, dl, MVT::i40, Value, Part);
		}
	}
	InVals.push_back(Value);
  }

  return Chain;
}

//===----------------------------------------------------------------------===//
//               Return Value Calling Convention Implementation
//===----------------------------------------------------------------------===//

bool TeakTargetLowering::CanLowerReturn(
	CallingConv::ID CallConv, MachineFunction &MF, bool isVarArg,
	const SmallVectorImpl<ISD::OutputArg> &Outs, LLVMContext &Context) const {
  SmallVector<CCValAssign, 16> RVLocs;
  CCState CCInfo(CallConv, isVarArg, MF, RVLocs, Context);
  if (!CCInfo.CheckReturn(Outs, RetCC_Teak)) {
	return false;
  }
  if (CCInfo.getNextStackOffset() != 0 && isVarArg) {
	return false;
  }
  return true;
}

SDValue
TeakTargetLowering::LowerReturn(SDValue Chain, CallingConv::ID CallConv,
								bool isVarArg,
								const SmallVectorImpl<ISD::OutputArg> &Outs,
								const SmallVectorImpl<SDValue> &OutVals,
								const SDLoc &dl, SelectionDAG &DAG) const {
  // CCValAssign - represent the assignment of
  // the return value to a location
  SmallVector<CCValAssign, 16> RVLocs;

  // CCState - Info about the registers and stack slot.
  CCState CCInfo(CallConv, isVarArg, DAG.getMachineFunction(), RVLocs,
				 *DAG.getContext());

  CCInfo.AnalyzeReturn(Outs, RetCC_Teak);

  SDValue Flag;
  SmallVector<SDValue, 4> RetOps(1, Chain);

  // Copy the result values into the output registers.
  for (unsigned i = 0, e = RVLocs.size(); i < e; ++i) {
	CCValAssign &VA = RVLocs[i];
	assert(VA.isRegLoc() && "Can only return in registers!");

	Chain = DAG.getCopyToReg(Chain, dl, VA.getLocReg(), OutVals[i], Flag);

	Flag = Chain.getValue(1);
	RetOps.push_back(DAG.getRegister(VA.getLocReg(), VA.getLocVT()));
  }

  RetOps[0] = Chain; // Update chain.

  // Add the flag if we have it.
  if (Flag.getNode()) {
	RetOps.push_back(Flag);
  }

  return DAG.getNode(TeakISD::RET_FLAG, dl, MVT::Other, RetOps);
}

void TeakTargetLowering::ReplaceNodeResults(SDNode *N,
											SmallVectorImpl<SDValue> &Results,
											SelectionDAG &DAG) const
{
	if (N->getOpcode() == ISD::LOAD && N->getValueType(0) == MVT::i64) {
		LoadSDNode *Load = cast<LoadSDNode>(N);
		if (Load->getMemoryVT() != MVT::i64 || Load->isAtomic() || Load->isIndexed())
			return;
		SDLoc Location(N);
		assert(Load->getMemoryVT() == MVT::i64 && !Load->isAtomic());
		SDValue Words[4], Chain = Load->getChain();
		for (unsigned Index = 0; Index < 4; ++Index) {
			SDValue Address = DAG.getMemBasePlusOffset(Load->getBasePtr(), Index, Location);
			SDValue Word = DAG.getLoad(MVT::i16, Location, Chain, Address,
				Load->getPointerInfo().getWithOffset(Index * 2),
				MinAlign(Load->getAlignment(), Index * 2),
				Load->getMemOperand()->getFlags(), Load->getAAInfo());
			Words[Index] = DAG.getNode(ISD::ZERO_EXTEND, Location, MVT::i40, Word);
			Chain = Word.getValue(1);
		}
		auto ShiftLeft = [&](SDValue Value, unsigned Shift) {
			return DAG.getNode(ISD::SHL, Location, MVT::i40, Value,
				DAG.getConstant(Shift, Location, MVT::i40));
		};
		SDValue High = DAG.getNode(ISD::OR, Location, MVT::i40,
			ShiftLeft(Words[0], 8), DAG.getNode(ISD::SRL, Location, MVT::i40, Words[1],
				DAG.getConstant(8, Location, MVT::i40)));
		SDValue Low = DAG.getNode(ISD::OR, Location, MVT::i40, Words[3],
			DAG.getNode(ISD::OR, Location, MVT::i40,
				ShiftLeft(Words[1], 32), ShiftLeft(Words[2], 16)));
		Results.append({Low, High, Chain});
		return;
	}
	dbgs() << "Opcode = " << N->getOpcode();
	//DAG.dump();
	//N->dumpr(&DAG);
	SDLoc dl(N);
	// if(N->getOpcode() == ISD::GlobalAddress)
	// {
	// 	GlobalAddressSDNode *GlobalAddr = cast<GlobalAddressSDNode>(N);
	// 	SDValue TargetAddr =
	// 		DAG.getTargetGlobalAddress(GlobalAddr->getGlobal(), dl, MVT::i40);
	// 	Results.push_back(TargetAddr); // DAG.getConstant(0, dl, MVT::i40));
	// 	//Results.push_back(DAG.getNode(ISD::ZERO_EXTEND, dl, MVT::i40,
	// 	//N->getOperand(0)));
	// 	return;
	// }

	// dbgs() << "ReplaceNodeResults not implemented for this op!\n";

	SDValue Res = LowerOperation(SDValue(N, 0), DAG);
	if (N->getOpcode() == ISD::GlobalAddress && N->getValueType(0) == MVT::i32)
		Res = DAG.getNode(ISD::TRUNCATE, dl, MVT::i32, Res);

    for (unsigned I = 0, E = Res->getNumValues(); I != E; ++I)
      Results.push_back(Res.getValue(I));

	// SDValue InOp = N->getOperand(0);
	// InOp.dump();
	// EVT InVT = InOp.getValueType();
	// dbgs() << "evt: " << InVT.getEVTString();

	// Results[0].dump();
	//llvm_unreachable("ReplaceNodeResults not implemented for this target!");
}

MachineBasicBlock* TeakTargetLowering::EmitInstrWithCustomInserter(MachineInstr &MI, MachineBasicBlock *BB) const
{
	switch (MI.getOpcode())
	{
		default:
			llvm_unreachable("Unknown SELECT_CC!");
		case Teak::SELECT_CC_Int_ICC:
		case Teak::SELECT_CC_Int_ICC_i16:
			return ExpandSelectCC(MI, BB, Teak::BRRCond_rel7);
	}
}

MachineBasicBlock* TeakTargetLowering::ExpandSelectCC(MachineInstr &MI, MachineBasicBlock *BB, unsigned BROpcode) const
{
	const TargetInstrInfo &TII = *Subtarget.getInstrInfo();
	DebugLoc dl = MI.getDebugLoc();
	unsigned CC = (TeakCC::CondCodes)MI.getOperand(3).getImm();

	// To "insert" a SELECT_CC instruction, we actually have to insert the
	// triangle control-flow pattern. The incoming instruction knows the
	// destination vreg to set, the condition code register to branch on, the
	// true/false values to select between, and the condition code for the branch.
	//
	// We produce the following control flow:
	//     ThisMBB
	//     |  \
	//     |  IfFalseMBB
	//     | /
	//    SinkMBB
	const BasicBlock *LLVM_BB = BB->getBasicBlock();
	MachineFunction::iterator It = ++BB->getIterator();

	MachineBasicBlock *ThisMBB = BB;
	MachineFunction *F = BB->getParent();
	MachineBasicBlock *IfFalseMBB = F->CreateMachineBasicBlock(LLVM_BB);
	MachineBasicBlock *SinkMBB = F->CreateMachineBasicBlock(LLVM_BB);
	F->insert(It, IfFalseMBB);
	F->insert(It, SinkMBB);

	// Transfer the remainder of ThisMBB and its successor edges to SinkMBB.
	SinkMBB->splice(SinkMBB->begin(), ThisMBB, std::next(MachineBasicBlock::iterator(MI)), ThisMBB->end());
	SinkMBB->transferSuccessorsAndUpdatePHIs(ThisMBB);

	// Set the new successors for ThisMBB.
	ThisMBB->addSuccessor(IfFalseMBB);
	ThisMBB->addSuccessor(SinkMBB);

	BuildMI(ThisMBB, dl, TII.get(BROpcode))
		.addMBB(SinkMBB)
		.addImm(CC);
		//.addReg(Teak::ICC, RegState::Implicit);
		//.addReg(Teak::ICC, RegState::Implicit);

	// IfFalseMBB just falls through to SinkMBB.
	IfFalseMBB->addSuccessor(SinkMBB);

	// %Result = phi [ %TrueValue, ThisMBB ], [ %FalseValue, IfFalseMBB ]
	BuildMI(*SinkMBB, SinkMBB->begin(), dl, TII.get(Teak::PHI), MI.getOperand(0).getReg())
		.addReg(MI.getOperand(1).getReg())
		.addMBB(ThisMBB)
		.addReg(MI.getOperand(2).getReg())
		.addMBB(IfFalseMBB);

	MI.eraseFromParent(); // The pseudo instruction is gone now.
	return SinkMBB;
}
