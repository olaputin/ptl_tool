% include('header.tpl')

<div class="jobs_status">
    <div class="col-md-6">
    <div class="row">
            <div class="col-md-1 header">Id</div>
            <div class="col-md-2 header">origin</div>
            <div class="col-md-5 header">created_at</div>
            <div class="col-md-3 header">status</div>
    </div>

    % for i, item in enumerate(jobs, 1):
    <div class="row job">
            <div class="col-md-1" id="{{item['id']}}">{{i}}</div>
            <div class="col-md-2">{{item['origin']}}</div>
            <div class="col-md-5">{{item['created_at']}}</div>
            <div class="col-md-3 {{item['status']}} status">{{item['status']}}</div>
    </div>
    % end
        </div>
</div>