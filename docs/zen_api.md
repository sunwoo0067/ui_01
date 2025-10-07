젠트레이드 상품데이터를 XML형태로 API연동을 진행할 수 있도록 지원합니다.
상품API연동 URL	https://www.zentrade.co.kr/shop/proc/product_api.php
※ 상품API연동 XML 데이터에는 상품 판매에 필요한 대부분의 데이터가 포함되어 있으며, 데이터 다운로드 및 가공은 귀사에서 직집 개발 및 적용하셔야 합니다.
▼상품API연동 파라미터 정보 (get/post 모두 이용가능) * 필수변수
변수명	필수	값 정보
id *	필수	b00679540
m_skey *	필수	5284c44b0fcf0f877e6791c5884d6ea9
goodsno	선택	젠트레이드 상품번호. goodsno 값을 전송하면 해당 상품 1개의 정보만 리턴됩니다.
runout	선택	품절여부.
1 : 품절상품만 검색
0 : 정상인 제품만 검색
(옵션품절은 지원하지 않습니다.)
opendate_s
opendate_e
선택	신상품오픈일자(검색 시작일/검색 종료일).
yyyy-MM-dd 형식으로 사용. (예: 2020-09-01)
opendate_s (검색 시작일) 와 opendate_e (검색 종료일) 가 모두 있어야 검색가능.
※ 필수변수는 상품API 연동을 위해 꼭 필요한 변수입니다. 선택변수는 선택적으로 필요에 따라 사용하시면 됩니다.
▼상품API연동 XML정보 예시

    <?xml version="1.0" encoding="euc-kr"?>
    <zentrade version="ZENTRADE XML 1.0" datetime="">
        <product code="젠트레이드 상품번호">
        <dome_category dome_catecode="젠트레이드 카테고리 코드">
            <![CDATA[ 젠트레이드 카테고리명  ]]>
        </dome_category>
        <scategory emp_catecode="플레이오토 EMP카테고리코드" esellers_catecode="이셀러스 카테고리코드" classcode="상품군코드" />
        <prdtname>
            <![CDATA[ 젠트레이드 상품명  ]]>
        </prdtname>
        <baseinfo madein="원산지" productcom="제조사" brand="브랜드" model="모델명" />
        <price buyprice="젠트레이드 판매가" consumerprice="소비자가" taxmode="과세여부(Y/N)" />
        <listimg url1="목록이미지1URL" url2="목록이미지2URL" url3="목록이미지3URL" url4="목록이미지4URL" url5="목록이미지5URL" />
        <option opt1nm="옵션명" opt2nm="2차옵션명(사용안함)">
            <![CDATA[ 옵션항목1^|^옵션항목1 판매가^|^옵션항목1 소비자가^|^옵션항목1 옵션이미지URL↑=↑
                    옵션항목2^|^옵션항목2 판매가^|^옵션항목2 소비자가^|^옵션항목2 옵션이미지URL↑=↑
                    ...  ]]>
        </option>
        <content>
            <![CDATA[ 상세페이지 이미지 소스  ]]>
        </content>
        <keyword>
            <![CDATA[ 키워드(쉼표로 구분)  ]]>
        </keyword>
        <status runout="품절여부(1:품절, 0:정상)" opendate="신상품 오픈일자" />
        </product>
        
        <product code="3">
        <dome_category dome_catecode="011">
            <![CDATA[ 패션/이미용/건강  ]]>
        </dome_category>
        <scategory emp_catecode="18120300" esellers_catecode="17440401" classcode="35" />
        <prdtname>
            <![CDATA[ [API연동테스트]40P 스마일뺏지 3cm/4.5cm  ]]>
        </prdtname>
        <baseinfo madein="상세정보참조" productcom="상세정보참조" brand="" model="" />
        <price buyprice="2100" consumerprice="0" taxmode="Y" />
        <listimg url1="https://www.zentrade.co.kr/shop/data/goods/144178309580l0.jpg" url2="https://www.zentrade.co.kr/shop/data/goods/1441783095206l1.jpg" 
                    url3="https://www.zentrade.co.kr/shop/data/goods/1438678401821l2.jpg" url4="https://www.zentrade.co.kr/shop/data/goods/1438678401964l3.jpg" 
                    url5="https://www.zentrade.co.kr/shop/data/goods/1438678401846l4.jpg" />
        <option opt1nm="사이즈" opt2nm="">
            <![CDATA[ 3cm-일반형^|^2100^|^0^|^https://www.zentrade.co.kr/shop/data/goods/1450070850875g0.jpg↑=↑
                    4.5cm-일반형^|^3500^|^0^|^https://www.zentrade.co.kr/shop/data/goods/1450070850331g1.jpg↑=↑
                    3cm-깜찍이형^|^2100^|^0^|^https://www.zentrade.co.kr/shop/data/goods/1450070850228g2.jpg↑=↑
                    4.5cm-깜찍이형^|^3500^|^0^|^https://www.zentrade.co.kr/shop/data/goods/1450070850939g3.jpg  ]]>
        </option>
        <content>
            <![CDATA[ <p align="center">
                            <img src="http://ai.esmplus.com/hoon392/product/zt/3/40smilebadge01.jpg"><br>
                            <img src="http://ai.esmplus.com/hoon392/product/zt/3/40smilebadge02.jpg"><br>
                            <img src="http://ai.esmplus.com/hoon392/product/zt/3/40smilebadge03.jpg"><br>
                            <img src="http://ai.esmplus.com/hoon392/product/zt/3/40smilebadge04.jpg"><br>
                            <img src="http://ai.esmplus.com/hoon392/product/zt/3/40smilebadge05.jpg"><br>
                            <img src="http://ai.esmplus.com/hoon392/product/zt/3/40smilebadge06.jpg"><br>
                            <img src="http://ai.esmplus.com/hoon392/product/zt/3/40smilebadge07.jpg"><br>
                            <img src="http://ai.esmplus.com/hoon392/product/zt/3/40smilebadge08.jpg"><br>
                            <img src="http://ai.esmplus.com/hoon392/product/zt/notice.jpg">
                            </p>  ]]>
        </content>
        <keyword>
            <![CDATA[ 뺏지,스마일뺏지,뱃지,브로치,와펜,스마일뱃지,스마일핀,스마일브로치,스마일와펜,버튼뱃지,배지,악세사리뺏지  ]]>
        </keyword>
        <status runout="0" opendate="2020-12-31" />
        </product>
        
        <product>
               ...
               ...
        </product>
    </zentrade>

젠트레이드에 주문한 내역을 XML형태로 API연동을 진행할 수 있도록 지원합니다.
주문조회 API연동 URL	https://www.zentrade.co.kr/shop/proc/order_api.php
※ 주문조회 API연동 XML 데이터에는 일반적인 주문내역과 송장정보 등의 데이터가 포함되어 있습니다. 해당 내역을 받아 처리하는 작업은 직집 개발 및 적용하셔야 합니다.
▼주문조회 API연동 파라미터 정보 (get/post 모두 이용가능) * 필수변수 * 선택적필수변수
변수명	필수	값 정보
id *	필수	b00679540
m_skey *	필수	5284c44b0fcf0f877e6791c5884d6ea9
ordno *	선택적필수	13자리로 구성된 젠트레이드 주문번호 (ordno 또는 pordno 둘중 한가지는 필수입니다.)
pordno *	선택적필수	젠트레이드로 주문등록시 입력한 개인고유주문번호 (ordno 또는 pordno 둘중 한가지는 필수입니다.)
※ 필수변수는 상품API 연동을 위해 꼭 필요한 변수입니다. 선택변수는 선택적으로 필요에 따라 사용하시면 됩니다.
▼주문조회 API연동 XML정보 예시

    <?xml version="1.0" encoding="euc-kr"?>
    <zentrade version="ZENTRADE ORDER XML 1.0" datetime="">
        <ord_info ordno="젠트레이드 주문번호" pordno="젠트레이드에 주문등록시 입력한 개인고유주문번호">
        <ord_date>주문일시</ord_date>
        <nameReceiver>
        	<![CDATA[ 받는사람 이름  ]]>
        </nameReceiver>
        <phoneReceiver>
        	<![CDATA[ 받는사람 전화번호  ]]>
        </phoneReceiver>
        <mobileReceiver>
        	<![CDATA[ 받는사람 핸드폰번호  ]]>
        </mobileReceiver>
        <address>
        	<![CDATA[ 받는사람 주소  ]]>
        </address>
        <ord_item1>
        	<![CDATA[ 젠트레이드 상품번호 - 상품명 / 옵션  ]]>
        </ord_item1>
        <ord_item2>
        	<![CDATA[ 젠트레이드 상품번호 - 상품명 / 옵션  ]]>
        </ord_item2>
             ...
             ...
        <deli_info delicom="택배회사" delinum="송장번호" />
        <zentrade_msg>
        	<![CDATA[ 젠트레이드 관리자 전달 메모  ]]>
        </zentrade_msg>
        </ord_info>        
    </zentrade>
