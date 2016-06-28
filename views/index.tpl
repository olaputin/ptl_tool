% include('header.tpl')

<div class="jobs_status">
    <div class="row">
        <div class="col-md-4 header">Id</div>
        <div class="col-md-2 header">origin</div>
        <div class="col-md-3 header">created_at</div>
        <div class="col-md-3 header">status</div>
    </div>

    % for item in jobs:
    <div class="row job">
        <div class="col-md-4">{{item['id']}}</div>
        <div class="col-md-2">{{item['origin']}}</div>
        <div class="col-md-3">{{item['created_at']}}</div>
        <div class="col-md-3 {{item['status']}} status">{{item['status']}}</div>
    </div>
    % end
</div>