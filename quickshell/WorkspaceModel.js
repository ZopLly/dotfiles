.pragma library
function groups(workspaces, applications, output) {
    let windows=[]
    for(let app of applications || [])
        for(let window of app.windows || [])
            windows.push(Object.assign({},window,{icon:app.icon,name:app.name,groupId:app.id}))
    return (workspaces || []).filter(w => w.output===output).sort((a,b)=>a.idx-b.idx).map(space => {
        let items=windows.filter(w => w.workspace_id===space.id)
        items.sort((a,b)=> {
            let ap=a.layout?.pos_in_scrolling_layout,bp=b.layout?.pos_in_scrolling_layout
            return ap && bp ? ap[0]-bp[0] || ap[1]-bp[1] || a.id-b.id : a.id-b.id
        })
        return Object.assign({},space,{windows:items,width:Math.max(28,items.length*32+12)})
    })
}
