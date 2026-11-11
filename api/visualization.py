"""Visualization data derived on the server from the same validated SI inputs.

No CFD. Tank dimensions and Bernoulli connector length are display choices, not
new physical boundary conditions. Chart samples delegate to the physics engine.
"""
from math import sqrt, sin, cos, pi, isfinite
from fluidlab_physics import hydrostatic_pressure, buoyancy, NumericalError

def text(en, fa):
    return {'en':en,'fa':fa}

def visualization(module, p, result):
    """Return SI scene geometry, vector magnitudes and scientific chart samples."""
    v={k:q.value for k,q in result.values.items()}
    shapes=[]; markers=[]; arrows=[]; charts=[]; notes=[]; flow=None; pressure_scale=None
    def box(key, size, position, color, opacity=1, angle=0):
        shapes.append(dict(kind='box',key=key,size=size,position=position,color=color,opacity=opacity,angle=angle))
    def pressure_field(shape, axis, low, high):
        # End values along the shape's local axis; these models vary linearly.
        shape['pressure'] = dict(axis=axis, values=[low, high])
    def scale(values, en, fa):
        return dict(min=min(values), max=max(values), unit='Pa', label=text(en, fa))
    def marker(position, en, fa, color='#e5a442'):
        markers.append(dict(position=position,label=text(en,fa),color=color))
    def arrow(origin, direction, magnitude, unit, group, en, fa, color):
        arrows.append(dict(origin=origin,direction=direction,magnitude=magnitude,unit=unit,group=group,label=text(en,fa),color=color))
    def chart(en,fa,xlabel,xfa,xunit,ylabel,yfa,yunit,series):
        charts.append(dict(title=text(en,fa),xLabel=text(xlabel,xfa),xUnit=xunit,yLabel=text(ylabel,yfa),yUnit=yunit,series=series))
    def series(en,fa,x,y,mode='lines'):
        return dict(label=text(en,fa),x=x,y=y,mode=mode)
    if module=='bernoulli':
        r1=sqrt(p['area1']/pi);r2=sqrt(p['area2']/pi)
        span=max(r1,r2)*10
        a=[-span/2,p['elevation1'],0];b=[span/2,p['elevation2'],0]
        shapes.append(dict(kind='pipe',key='pipe',start=a,end=b,radius1=r1,radius2=r2,color='#2c92aa',opacity=.3))
        marker(a,'Station 1','مقطع ۱');marker(b,'Station 2','مقطع ۲','#ad84c2')
        flow=dict(start=a,end=b,radius1=r1,radius2=r2,active=p['flow_rate']>0)
        p1=p['pressure1']+(p['reference_pressure'] if p['pressure_basis']=='gauge' else 0)
        pressure_scale=scale([p1,v['pressure2_absolute']], 'Absolute pressure at solved stations', 'فشار مطلق در مقاطع حل‌شده')
        for index, (point, radius, pressure) in enumerate([(a,r1,p1),(b,r2,v['pressure2_absolute'])]):
            # Short station bands only: no inferred interior pressure field.
            direction=[(b[j]-a[j]) for j in range(3)]
            norm=sqrt(sum(d*d for d in direction))
            half=min(r1,r2)*.08
            start=[point[j]-direction[j]/norm*half for j in range(3)]
            end=[point[j]+direction[j]/norm*half for j in range(3)]
            shapes.append(dict(kind='pipe',key=f'pressure-station-{index}',start=start,end=end,radius1=radius*1.01,radius2=radius*1.01,color='#ffffff',opacity=1))
            pressure_field(shapes[-1], 'y', pressure, pressure)
        chart('Station pressures','فشار مقاطع','Station','مقطع','1','Absolute pressure','فشار مطلق','Pa',[series('Absolute pressure','فشار مطلق',[1,2],[p1,v['pressure2_absolute']],'markers')])
        chart('Station velocities','سرعت مقاطع','Station','مقطع','1','Mean velocity','سرعت میانگین','m/s',[series('Mean velocity','سرعت میانگین',[1,2],[v['velocity1'],v['velocity2']],'markers')])
        notes.append(text('Connector length and taper are schematic. Only the two stations are solved; interior pressure and velocity are not predicted.','طول اتصال و تغییر سطح مقطع شماتیک است. فقط دو مقطع حل شده‌اند؛ فشار و سرعت داخلی پیش‌بینی نمی‌شوند.'))
    elif module=='hydrostatics':
        length=p['length'];width=p['width'];theta=p['angle'];top=p['top_depth']
        bottom=top+length*sin(theta);depth=max(bottom,length*.3,width*.3)
        box('water',[length*1.5,depth,width*1.5],[length*cos(theta)/2,-depth/2,0],'#60b7d2',.15)
        box('surface',[length,max(length,width)*.015,width],[length*cos(theta)/2,-top-length*sin(theta)/2,0],'#7c899c',1,-theta)
        marker([0,-top,0],'Top edge','لبه بالا','#a38bca')
        start=min(length,max(0,-top/sin(theta))) if sin(theta) else (length if top<0 else 0)
        ss=[start+(length-start)*i/20 for i in range(21)] if start<length else []
        depths=[max(0,top+s*sin(theta)) for s in ss]
        pressures=[hydrostatic_pressure(h,p['density'],p['surface_pressure_absolute'],pressure_basis='absolute',reference_pressure=p['opposing_pressure_absolute'],gravity=p['gravity']).values['pressure_gauge'].value for h in depths]
        if pressures:
            pressure_scale=scale(pressures, 'Net pressure relative to opposing side', 'فشار خالص نسبت به سمت مقابل')
            middle=(start+length)/2
            box('surface-pressure',[length-start,max(length,width)*.015*1.02,width*1.002],[middle*cos(theta),-top-middle*sin(theta),0],'#ffffff',1,-theta)
            pressure_field(shapes[-1], 'x', pressures[0], pressures[-1])
        normal=[sin(theta),cos(theta),0]
        for i in range(0,len(ss),4):
            arrow([ss[i]*cos(theta),-top-ss[i]*sin(theta),0],normal,pressures[i],'Pa','pressure','Net pressure','فشار خالص','#38a2c0')
        cp=v['resultant_distance']
        if cp is not None:
            position=[cp*cos(theta),-top-cp*sin(theta),0]
            if abs(cp)<length*10:
                marker(position,'Center of pressure','مرکز فشار','#ef9f39')
                arrow(position,normal,v['force'],'N','force','Resultant force','نیروی برآیند','#ef9f39')
            else:
                notes.append(text('Resultant lies far outside the surface and is omitted from the scene; use its numerical location.','برآیند بسیار دور از سطح است و در صحنه نمایش داده نمی‌شود؛ موقعیت عددی را بررسی کنید.'))
        chart('Net pressure on wetted surface','فشار خالص روی سطح خیس‌شده','Distance from top edge','فاصله از لبه بالا','m','Net pressure','فشار خالص','Pa',[series('Net pressure','فشار خالص',ss,pressures)])
        notes.append(text('Pressure is relative to opposing pressure. Pressure arrows and resultant force use separate display scales; tank dimensions are schematic.','فشار نسبت به فشار سمت مقابل است. پیکان‌های فشار و نیروی برآیند مقیاس نمایشی جدا دارند؛ ابعاد مخزن شماتیک است.'))
    elif module=='pipe-flow':
        radius=p['diameter']/2;length=p['length']
        # Diameter magnification avoids an invisible tube on very slender pipelines.
        display_radius=sqrt(radius)*sqrt(max(radius,length/5))
        a=[-length/2,0,0];b=[length/2,0,0]
        if length==0:a=[-radius,0,0];b=[radius,0,0]
        known=v['major_head_loss'] is not None
        for i in range(20):
            start=[a[0]+(b[0]-a[0])*i/20,0,0];end=[a[0]+(b[0]-a[0])*(i+1)/20,0,0]
            shapes.append(dict(kind='pipe',key=f'pipe-{i}',start=start,end=end,radius1=display_radius,radius2=display_radius,color=(f'hsl({190-i*3}, 55%, 55%)' if known and p['flow_rate']>0 and length>0 else '#8297a4'),opacity=.55))
        marker(a,'Inlet','ورودی');marker(b,'Outlet','خروجی','#ad84c2')
        flow=dict(start=a,end=b,radius1=display_radius,radius2=display_radius,active=p['flow_rate']>0)
        x=[length*i/20 for i in range(21)]
        loss=[p['density']*p['gravity']*v['major_head_loss']*i/20 for i in range(21)] if known else [None]*21
        if known:
            major=loss[-1]
            pressure_scale=scale([-major,0], 'Pressure change from inlet: major friction only', 'تغییر فشار نسبت به ورودی: فقط اصطکاک اصلی')
            for i, shape in enumerate(shapes):
                pressure_field(shape, 'y', -major*i/20, -major*(i+1)/20)
                shape['opacity']=1
            x.append(length);loss.append(v['pressure_loss'])
        chart('Accumulated pressure loss','افت فشار تجمعی','Axial distance','فاصله محوری','m','Pressure loss','افت فشار','Pa',[series('Loss from inlet','افت از ورودی',x,loss)])
        notes.append(text('Surface color shows pressure change relative to inlet due to major friction only, not absolute pressure. Minor losses are lumped at the outlet in the chart only.','رنگ سطح تغییر فشار نسبت به ورودی بر اثر اصطکاک اصلی است، نه فشار مطلق. افت‌های موضعی فقط در نمودار در خروجی جمع شده‌اند.'))
        if display_radius!=radius or length==0:
            notes.append(text('Pipe diameter is magnified or zero length is expanded for visibility; use the input dimensions for engineering values.','قطر بزرگ‌نمایی شده یا طول صفر برای دید بهتر گسترش یافته است؛ مقادیر مهندسی را از ورودی‌ها بخوانید.'))
    else:
        height=p['body_volume']/p['base_area'];side=sqrt(p['base_area'])
        displacement=v['equilibrium_displacement']
        immersion=v['draft'] if v['draft'] is not None else height
        center=height/2-immersion
        box('water',[side*3,max(height*1.6,side),side*3],[0,-max(height*1.6,side)/2,0],'#60b7d2',.15)
        box('body',[side,height,side],[0,center,0],'#7c899c',1)
        if immersion>0:
            # Hydrostatic pressure difference Δp = rho*g*h; no absolute pressure assumed.
            low=p['fluid_density']*p['gravity']*immersion
            pressure_scale=scale([0,low], 'Hydrostatic pressure above free-surface pressure', 'فشار هیدروستاتیکی نسبت به سطح آزاد')
            box('body-pressure',[side*1.002,immersion,side*1.002],[0,-immersion/2,0],'#ffffff',1)
            pressure_field(shapes[-1], 'y', low, 0)
            notes.append(text('Pressure colors apply only to the wetted body. Dry surfaces are gray. For sinking/neutral bodies, pressure corresponds to the illustrative immersion shown.', 'رنگ فشار فقط روی بخش خیس‌شدهٔ جسم است؛ سطح خشک خاکستری است. برای جسم فرورونده یا خنثی، فشار مربوط به عمق نمایشی فعلی است.'))
        actual_volume=p['body_volume'] if displacement is None else displacement
        forces=buoyancy(actual_volume,p['body_volume'],p['mass'],p['fluid_density'],p['gravity'])
        arrow([side*.6,center,0],[0,-1,0],forces.values['weight'].value,'N','force','Weight','وزن','#d96d59')
        arrow([-side*.6,-immersion/2,0],[0,1,0],forces.values['buoyant_force'].value,'N','force','Buoyant force','نیروی شناوری','#2fa8b5')
        marker([0,-immersion/2,0],'Center of buoyancy','مرکز شناوری','#2fa8b5')
        depths=[height*i/20 for i in range(21)]
        fb=[buoyancy(min(p['body_volume'],p['base_area']*d),p['body_volume'],p['mass'],p['fluid_density'],p['gravity']).values['buoyant_force'].value for d in depths]
        chart('Buoyancy versus immersion','شناوری بر حسب عمق غوطه‌وری','Immersion depth','عمق غوطه‌وری','m','Force','نیرو','N',[series('Buoyant force','نیروی شناوری',depths,fb),series('Weight','وزن',depths,[forces.values['weight'].value]*len(depths))])
        notes.append(text('Square-base upright prism. Weight acts at the assumed geometric center of gravity; arrows are offset sideways for readability. Tank size is schematic.','منشور قائم با قاعده مربع. مرکز ثقل در مرکز هندسی فرض شده؛ پیکان‌ها برای خوانایی به طرفین منتقل شده‌اند. اندازه مخزن شماتیک است.'))
        if result.status in ('neutral','no_equilibrium'):
            notes.append(text('Shown fully submerged at an illustrative position, not a predicted equilibrium depth or sinking trajectory.','جسم کاملاً غوطه‌ور در موقعیتی نمایشی است؛ عمق تعادل یا مسیر فرورفتن پیش‌بینی نشده است.'))
    packet=dict(pressureScale=pressure_scale,shapes=shapes,markers=markers,arrows=arrows,flow=flow,charts=charts,notes=notes)
    def finite(value):
        if isinstance(value,float) and not isfinite(value):
            raise NumericalError('Visualization sample exceeded finite numerical range')
        if isinstance(value,dict):
            for child in value.values(): finite(child)
        elif isinstance(value,list):
            for child in value: finite(child)
    finite(packet)
    return packet
