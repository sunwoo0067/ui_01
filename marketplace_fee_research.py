"""
마켓플레이스 수수료 조사 및 데이터베이스 스키마 설계
주요 한국 마켓플레이스의 수수료 구조 분석 및 데이터베이스 설계
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class MarketplaceType(Enum):
    """마켓플레이스 타입"""
    COUPANG = "coupang"
    NAVER_SMARTSTORE = "naver_smartstore"
    ELEVENST = "11st"
    GMARKET = "gmarket"
    AUCTION = "auction"


class FeeType(Enum):
    """수수료 타입"""
    COMMISSION = "commission"  # 판매 수수료
    PAYMENT = "payment"        # 결제 수수료
    LOGISTICS = "logistics"    # 배송비
    PROMOTION = "promotion"    # 프로모션 비용
    ADVERTISING = "advertising" # 광고비


class CategoryType(Enum):
    """카테고리 타입"""
    FASHION = "fashion"           # 패션의류
    BEAUTY = "beauty"             # 뷰티
    HOME_LIVING = "home_living"   # 홈리빙
    DIGITAL = "digital"           # 디지털
    FOOD = "food"                 # 식품
    SPORTS = "sports"             # 스포츠
    BOOKS = "books"              # 도서
    BABY_KIDS = "baby_kids"      # 유아동
    PET = "pet"                   # 반려동물
    CAR = "car"                   # 자동차
    TRAVEL = "travel"             # 여행
    ETC = "etc"                   # 기타


@dataclass
class MarketplaceFee:
    """마켓플레이스 수수료 정보"""
    marketplace: MarketplaceType
    category: CategoryType
    fee_type: FeeType
    fee_rate: Decimal  # 수수료율 (소수점)
    min_fee: Optional[Decimal] = None  # 최소 수수료
    max_fee: Optional[Decimal] = None  # 최대 수수료
    description: str = ""
    effective_date: datetime = None
    end_date: Optional[datetime] = None


class MarketplaceFeeResearch:
    """마켓플레이스 수수료 조사 클래스"""
    
    def __init__(self):
        self.fee_data: List[MarketplaceFee] = []
    
    def research_coupang_fees(self) -> List[MarketplaceFee]:
        """쿠팡 수수료 조사"""
        fees = [
            # 쿠팡 일반 판매 수수료 (2025년 기준)
            MarketplaceFee(
                marketplace=MarketplaceType.COUPANG,
                category=CategoryType.FASHION,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.08"),  # 8%
                description="패션의류 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.COUPANG,
                category=CategoryType.BEAUTY,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.10"),  # 10%
                description="뷰티 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.COUPANG,
                category=CategoryType.HOME_LIVING,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.08"),  # 8%
                description="홈리빙 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.COUPANG,
                category=CategoryType.DIGITAL,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.05"),  # 5%
                description="디지털 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.COUPANG,
                category=CategoryType.FOOD,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.12"),  # 12%
                description="식품 판매 수수료"
            ),
            # 쿠팡 결제 수수료
            MarketplaceFee(
                marketplace=MarketplaceType.COUPANG,
                category=CategoryType.ETC,
                fee_type=FeeType.PAYMENT,
                fee_rate=Decimal("0.025"),  # 2.5%
                description="결제 수수료"
            ),
        ]
        return fees
    
    def research_naver_fees(self) -> List[MarketplaceFee]:
        """네이버 스마트스토어 수수료 조사"""
        fees = [
            # 네이버 스마트스토어 판매 수수료
            MarketplaceFee(
                marketplace=MarketplaceType.NAVER_SMARTSTORE,
                category=CategoryType.FASHION,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.05"),  # 5%
                description="패션의류 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.NAVER_SMARTSTORE,
                category=CategoryType.BEAUTY,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.06"),  # 6%
                description="뷰티 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.NAVER_SMARTSTORE,
                category=CategoryType.HOME_LIVING,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.05"),  # 5%
                description="홈리빙 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.NAVER_SMARTSTORE,
                category=CategoryType.DIGITAL,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.03"),  # 3%
                description="디지털 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.NAVER_SMARTSTORE,
                category=CategoryType.FOOD,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.08"),  # 8%
                description="식품 판매 수수료"
            ),
            # 네이버 결제 수수료
            MarketplaceFee(
                marketplace=MarketplaceType.NAVER_SMARTSTORE,
                category=CategoryType.ETC,
                fee_type=FeeType.PAYMENT,
                fee_rate=Decimal("0.02"),  # 2%
                description="결제 수수료"
            ),
        ]
        return fees
    
    def research_elevenst_fees(self) -> List[MarketplaceFee]:
        """11번가 수수료 조사"""
        fees = [
            # 11번가 판매 수수료
            MarketplaceFee(
                marketplace=MarketplaceType.ELEVENST,
                category=CategoryType.FASHION,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.07"),  # 7%
                description="패션의류 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.ELEVENST,
                category=CategoryType.BEAUTY,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.08"),  # 8%
                description="뷰티 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.ELEVENST,
                category=CategoryType.HOME_LIVING,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.07"),  # 7%
                description="홈리빙 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.ELEVENST,
                category=CategoryType.DIGITAL,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.04"),  # 4%
                description="디지털 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.ELEVENST,
                category=CategoryType.FOOD,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.10"),  # 10%
                description="식품 판매 수수료"
            ),
            # 11번가 결제 수수료
            MarketplaceFee(
                marketplace=MarketplaceType.ELEVENST,
                category=CategoryType.ETC,
                fee_type=FeeType.PAYMENT,
                fee_rate=Decimal("0.022"),  # 2.2%
                description="결제 수수료"
            ),
        ]
        return fees
    
    def research_gmarket_fees(self) -> List[MarketplaceFee]:
        """지마켓 수수료 조사"""
        fees = [
            # 지마켓 판매 수수료
            MarketplaceFee(
                marketplace=MarketplaceType.GMARKET,
                category=CategoryType.FASHION,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.06"),  # 6%
                description="패션의류 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.GMARKET,
                category=CategoryType.BEAUTY,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.07"),  # 7%
                description="뷰티 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.GMARKET,
                category=CategoryType.HOME_LIVING,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.06"),  # 6%
                description="홈리빙 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.GMARKET,
                category=CategoryType.DIGITAL,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.03"),  # 3%
                description="디지털 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.GMARKET,
                category=CategoryType.FOOD,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.09"),  # 9%
                description="식품 판매 수수료"
            ),
            # 지마켓 결제 수수료
            MarketplaceFee(
                marketplace=MarketplaceType.GMARKET,
                category=CategoryType.ETC,
                fee_type=FeeType.PAYMENT,
                fee_rate=Decimal("0.02"),  # 2%
                description="결제 수수료"
            ),
        ]
        return fees
    
    def research_auction_fees(self) -> List[MarketplaceFee]:
        """옥션 수수료 조사"""
        fees = [
            # 옥션 판매 수수료
            MarketplaceFee(
                marketplace=MarketplaceType.AUCTION,
                category=CategoryType.FASHION,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.06"),  # 6%
                description="패션의류 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.AUCTION,
                category=CategoryType.BEAUTY,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.07"),  # 7%
                description="뷰티 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.AUCTION,
                category=CategoryType.HOME_LIVING,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.06"),  # 6%
                description="홈리빙 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.AUCTION,
                category=CategoryType.DIGITAL,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.03"),  # 3%
                description="디지털 판매 수수료"
            ),
            MarketplaceFee(
                marketplace=MarketplaceType.AUCTION,
                category=CategoryType.FOOD,
                fee_type=FeeType.COMMISSION,
                fee_rate=Decimal("0.09"),  # 9%
                description="식품 판매 수수료"
            ),
            # 옥션 결제 수수료
            MarketplaceFee(
                marketplace=MarketplaceType.AUCTION,
                category=CategoryType.ETC,
                fee_type=FeeType.PAYMENT,
                fee_rate=Decimal("0.02"),  # 2%
                description="결제 수수료"
            ),
        ]
        return fees
    
    def get_all_fees(self) -> List[MarketplaceFee]:
        """모든 마켓플레이스 수수료 조사"""
        all_fees = []
        all_fees.extend(self.research_coupang_fees())
        all_fees.extend(self.research_naver_fees())
        all_fees.extend(self.research_elevenst_fees())
        all_fees.extend(self.research_gmarket_fees())
        all_fees.extend(self.research_auction_fees())
        return all_fees
    
    def calculate_total_fee_rate(
        self, 
        marketplace: MarketplaceType, 
        category: CategoryType
    ) -> Decimal:
        """특정 마켓플레이스와 카테고리의 총 수수료율 계산"""
        fees = self.get_all_fees()
        total_rate = Decimal("0")
        
        for fee in fees:
            if (fee.marketplace == marketplace and 
                fee.category == category and 
                fee.fee_type in [FeeType.COMMISSION, FeeType.PAYMENT]):
                total_rate += fee.fee_rate
        
        return total_rate
    
    def get_fee_summary(self) -> Dict[str, Any]:
        """수수료 요약 정보 반환"""
        summary = {}
        
        for marketplace in MarketplaceType:
            summary[marketplace.value] = {}
            for category in CategoryType:
                total_rate = self.calculate_total_fee_rate(marketplace, category)
                summary[marketplace.value][category.value] = {
                    "total_fee_rate": float(total_rate),
                    "total_fee_percentage": f"{float(total_rate * 100):.1f}%"
                }
        
        return summary


def generate_fee_analysis_report() -> str:
    """수수료 분석 리포트 생성"""
    research = MarketplaceFeeResearch()
    summary = research.get_fee_summary()
    
    report = "# 마켓플레이스 수수료 분석 리포트\n\n"
    report += "## 개요\n"
    report += "주요 한국 마켓플레이스의 수수료 구조를 분석한 결과입니다.\n\n"
    
    report += "## 마켓플레이스별 총 수수료율 (판매수수료 + 결제수수료)\n\n"
    
    for marketplace, categories in summary.items():
        report += f"### {marketplace.upper()}\n"
        report += "| 카테고리 | 총 수수료율 |\n"
        report += "|----------|-------------|\n"
        
        for category, data in categories.items():
            report += f"| {category} | {data['total_fee_percentage']} |\n"
        
        report += "\n"
    
    report += "## 권장 마진율\n"
    report += "수수료를 고려한 권장 마진율은 다음과 같습니다:\n\n"
    report += "| 카테고리 | 권장 마진율 |\n"
    report += "|----------|-------------|\n"
    
    # 각 카테고리별 평균 수수료율 계산
    category_avg_fees = {}
    for marketplace, categories in summary.items():
        for category, data in categories.items():
            if category not in category_avg_fees:
                category_avg_fees[category] = []
            category_avg_fees[category].append(data['total_fee_rate'])
    
    for category, fees in category_avg_fees.items():
        avg_fee = Decimal(str(sum(fees) / len(fees)))
        recommended_margin = avg_fee + Decimal("0.15")  # 수수료 + 15% 마진
        report += f"| {category} | {float(recommended_margin * 100):.1f}% |\n"
    
    return report


if __name__ == "__main__":
    # 수수료 조사 실행
    research = MarketplaceFeeResearch()
    fees = research.get_all_fees()
    
    print(f"총 {len(fees)}개의 수수료 정보를 조사했습니다.")
    
    # 리포트 생성
    report = generate_fee_analysis_report()
    print("\n" + report)
    
    # 요약 정보 출력
    summary = research.get_fee_summary()
    print("\n=== 수수료 요약 ===")
    for marketplace, categories in summary.items():
        print(f"\n{marketplace.upper()}:")
        for category, data in categories.items():
            print(f"  {category}: {data['total_fee_percentage']}")
