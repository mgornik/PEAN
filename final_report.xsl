<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">
<html>
<body onload="onLoad();">
  <h1>Izveštaj o pregledu studentskih zadataka</h1>
  <input id="hide-all" type="button" style="width:150px" value="Sakrij sve detalje" onclick="return toggleAllDetails();"/>
  <p/>
  <table border="2">
    <xsl:for-each select="assignments/assignment">
      <tr>
        <table border="0">
          <xsl:variable name="bg-color">
            <xsl:choose>
              <xsl:when test="position() mod 2 = 0">#A9A9A9</xsl:when>
              <xsl:otherwise>#DCDCDC</xsl:otherwise>
            </xsl:choose>
          </xsl:variable>
          <tr class="header" bgcolor="{$bg-color}">
            <xsl:attribute name="style">
              <xsl:if test="status = &quot;skipped&quot;">
                background-color: #CC0000;
              </xsl:if>
            </xsl:attribute>
            <td style="font:size:18px" width="50px"><input id="toggle-{position()}" type="button" value="-" onclick="return toggleDetails(this);" style="width:30px"/><xsl:value-of select="position()"/></td>
            <td style="font-size:18px" width="200px">Br indeksa: <b><xsl:value-of select="id"/></b></td>
            <td style="font-size:18px" width="450px">Ime i prezime: <xsl:value-of select="name"/></td>
            <td style="font-size:18px; text-align: center" width="100px">Računar: <b><xsl:value-of select="@station"/></b></td>
            <td id="t-status-{position()}" style="font-size:18px" width="160px">
              <xsl:attribute name="style">
                <xsl:if test="status = &quot;ok&quot;">
                  background-color: #00CC22;
                  text-align: center;
                </xsl:if>
                <xsl:if test="status = &quot;directly-rated&quot;">
                  background-color: #0022FF;
                  text-align: center;
                </xsl:if>
                <xsl:if test="status = &quot;blocked&quot; or status = &quot;fails-to-compile&quot;">
                  background-color: #DD4144;
                  text-align: center;
                </xsl:if>
              </xsl:attribute>
              Status: <xsl:value-of select="status"/>
            </td>
            <td id="t-direct-score-{position()}" width="120px" style="text-align: center">Direktno: <xsl:value-of select="direct-score"/> %</td>
            <td id="t-test-score-{position()}" width="120px" style="text-align: center">Testovi: <xsl:value-of select="test-score"/> %</td>
            <td id="t-correction-{position()}" width="120px" style="text-align: center">Korekcija: <xsl:value-of select="correction"/> %</td>
            <td id="t-final-pct-{position()}" style="font-size:18px; text-align: center" width="130px" rowspan="2">Konačan: <b><xsl:value-of select="final-pct"/> %</b></td>
            <td style="font-size:18px; text-align: center" width="130px" rowspan="2">Bodovi: <b><xsl:value-of select="final-points"/></b></td>
          </tr>
          <tr bgcolor="{$bg-color}">
            <xsl:attribute name="style">
              <xsl:if test="status = &quot;skipped&quot;">
                background-color: #CC0000;
              </xsl:if>
            </xsl:attribute>
            <td id="t-comment-{position()}" colspan="4"><i>Komentar: <xsl:value-of select="comment"/></i></td>
            <td id="t-reason-{position()}" colspan="4"><i>Obrazloženje: <xsl:value-of select="reason"/></i></td>
          </tr>
          <tr>
            <td id="t-test-runs-{position()}" colspan="10">
              <table>
                <xsl:for-each select="tests/test">
                  <tr>
                    <td bgcolor="#95DBFE" style="font-size:16px; letter-spacing: -1px; padding-right:10px;">Naziv: <b><xsl:value-of select="@name"/></b></td>
                    <td bgcolor="#95DBFE">
                      <xsl:attribute name="style">
                        <xsl:if test="success = &quot;true&quot;">
                          font-size:16px;
                          letter-spacing: -1px;
                          background-color: #00CC22;
                          text-align: center;
                          padding-right:10px; 
                          padding-left:10px;
                        </xsl:if>
                        <xsl:if test="success = &quot;false&quot;">
                          font-size:16px;
                          letter-spacing: -1px;
                          background-color: #DD4144;
                          text-align: center;
                          padding-right:10px; 
                          padding-left:10px;
                        </xsl:if>
                      </xsl:attribute>
                      <xsl:choose>
                        <xsl:when test="success = &quot;true&quot;">Prošao</xsl:when>
                        <xsl:otherwise>Pao</xsl:otherwise>
                      </xsl:choose>
                    </td>
                    <xsl:variable name="passes-bg-color">
                      <xsl:choose>
                        <xsl:when test="passes &gt; 0">#00CC22</xsl:when>
                        <xsl:otherwise>#95DBFE</xsl:otherwise>
                      </xsl:choose>
                    </xsl:variable>
                    <td bgcolor="{$passes-bg-color}" style="font-size:16px; text-align: center; letter-spacing: -1px; padding-right:10px; padding-left:10px;">OK: <xsl:value-of select="passes"/>/<xsl:value-of select="runs"/></td>
                    <xsl:variable name="failures-bg-color">
                      <xsl:choose>
                        <xsl:when test="failures &gt; 0">#DD4144</xsl:when>
                        <xsl:otherwise>#95DBFE</xsl:otherwise>
                      </xsl:choose>
                    </xsl:variable>
                    <td bgcolor="{$failures-bg-color}" style="font-size:16px; text-align: center; letter-spacing: -1px; padding-right:10px; padding-left:10px;">KO: <xsl:value-of select="failures"/>/<xsl:value-of select="runs"/> (test: <xsl:value-of select="test-fails"/>, krah: <xsl:value-of select="crashes"/>, time-out: <xsl:value-of select="time-outs"/>)</td>
                    <td bgcolor="#95DBFE" style="font-size:16px; text-align: center; letter-spacing: -1px; padding-right:10px; padding-left:10px;">ukupno: <xsl:value-of select="total-duration"/>s, max: <xsl:value-of select="max-duration"/>s</td>
                    <td bgcolor="#95DBFE" style="font-size:16px; text-align: center; letter-spacing: -1px; padding-right:10px; padding-left:10px;">faktor: <xsl:value-of select="factor"/></td>
                    <td bgcolor="#95DBFE">
                    <xsl:attribute name="style">
                      <xsl:if test="success = &quot;true&quot;">
                        font-size:16px; 
                        text-align: center; 
                        letter-spacing: -1px; 
                        padding-right:10px; 
                        padding-left:10px;
                      </xsl:if>
                      <xsl:if test="success = &quot;false&quot;">
                        font-size:16px; 
                        text-align: center; 
                        letter-spacing: -1px; 
                        padding-right:10px; 
                        padding-left:10px;
                        text-decoration: line-through;
                      </xsl:if>
                    </xsl:attribute>
                    nosi: <xsl:value-of select="score"/> %</td>

                    <xsl:for-each select="executions/passed">
                      <a target="_blank" href="reports/{../../../../@station}/{../../@name}-{position()}.txt"> 
                        <td>
                        <xsl:attribute name="style">
                          <xsl:if test="current() = &quot;true&quot;">
                            background-color: #00CC22; 
                            font-size:12px; 
                            text-align: center; 
                            letter-spacing: -1px; 
                            padding-right:5px; 
                            padding-left:5px;
                          </xsl:if>
                          <xsl:if test="current() = &quot;false&quot;">
                            background-color: #DD4144;
                            font-size:12px; 
                            text-align: center; 
                            letter-spacing: -1px; 
                            padding-right:5px; 
                            padding-left:5px;
                          </xsl:if>
                        </xsl:attribute>
                        <xsl:value-of select="position()"/></td>
                      </a>
                    </xsl:for-each>
                  </tr>
                </xsl:for-each>
              </table>
            </td>
          </tr>
        </table>
      </tr>
      <tr height="10px"></tr>
    </xsl:for-each>
  </table>
  <script type="text/javascript">
function onLoad() {
  window.scroll(0, document.documentElement.scrollHeight);  
}

function toggleDetails(el) {
  var index = el.id.replace(new RegExp("^toggle-"), '');
  var suffix = '-' + index;
  if (el.value === '-') {
    el.value = '+';
    var disp = 'none';
  } else {
    el.value = '-';
    var disp = '';
  }

  var elements = document.querySelectorAll('td[id^="t-"]');
  for(var i=0;i&lt;elements.length;i++){
    if (elements[i].id.endsWith(suffix)) {
      document.getElementById(elements[i].id).style.display = disp;
    }
  }
}

var allDetails = 'expanded';

function toggleAllDetails() {
  if (allDetails === 'expanded') {
    document.getElementById('hide-all').value = 'Prikaži sve detalje';
    var disp = 'none';
    var toggle = '+';
  } else {
    document.getElementById('hide-all').value = 'Sakrij sve detalje';
    var disp = '';   
    var toggle = '-'; 
  }

  var elements = document.querySelectorAll('td[id^="t-"]');
  for(var i=0;i&lt;elements.length;i++){
    document.getElementById(elements[i].id).style.display = disp;
  }

  var elements = document.querySelectorAll('input[id^="toggle-"]');
  for(var i=0;i&lt;elements.length;i++){
    document.getElementById(elements[i].id).value = toggle;
  }

  allDetails = allDetails == 'expanded' ? 'collapsed' : 'expanded';
}
  </script>
</body>
</html>
</xsl:template>
</xsl:stylesheet>

