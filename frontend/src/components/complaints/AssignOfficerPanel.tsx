"use client";



import { useState } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { complaintsApi, staffApi } from "@/lib/api";

import { Button } from "@/components/ui/button";

import { cn } from "@/lib/utils";

import { Loader2, Mail, MapPin, Phone, UserCheck } from "lucide-react";

import type { Complaint } from "@/types";



export type DeptOfficerForAssign = {

  id: string;

  full_name: string;

  email?: string;

  phone?: string;

  service_area?: string;

  department_name?: string;

  department_code?: string;

  active_assigned_count?: number;

  critical_count?: number;

  high_count?: number;

  medium_count?: number;

  low_count?: number;

};



function PriorityWorkload({ o }: { o: DeptOfficerForAssign }) {

  const items = [

    { key: "critical", label: "Critical", count: o.critical_count ?? 0, className: "bg-red-100 text-red-800 ring-red-200" },

    { key: "high", label: "High", count: o.high_count ?? 0, className: "bg-amber-100 text-amber-900 ring-amber-200" },

    { key: "medium", label: "Medium", count: o.medium_count ?? 0, className: "bg-blue-100 text-blue-800 ring-blue-200" },

    { key: "low", label: "Low", count: o.low_count ?? 0, className: "bg-slate-100 text-slate-700 ring-slate-200" },

  ];

  return (

    <div className="flex flex-wrap gap-1.5 mt-2">

      {items.map(({ key, label, count, className }) => (

        <span

          key={key}

          className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1", className)}

        >

          {label}: {count}

        </span>

      ))}

    </div>

  );

}



export function AssignOfficerPanel({

  complaint,

  departmentId,

}: {

  complaint: Complaint;

  departmentId?: string;

}) {

  const queryClient = useQueryClient();

  const [officerId, setOfficerId] = useState(complaint.assigned_officer_id || "");



  const { data: officers = [], isLoading } = useQuery({

    queryKey: ["dept-officers", departmentId],

    queryFn: () => staffApi.listOfficers(departmentId).then((r) => r.data as DeptOfficerForAssign[]),

    enabled: !!departmentId,

  });



  const selected = officers.find((o) => o.id === officerId);



  const assign = useMutation({

    mutationFn: () => complaintsApi.assign(complaint.id, officerId),

    onSuccess: () => {

      queryClient.invalidateQueries({ queryKey: ["complaint", complaint.id] });

      queryClient.invalidateQueries({ queryKey: ["complaints"] });

      queryClient.invalidateQueries({ queryKey: ["complaint"] });

      queryClient.invalidateQueries({ queryKey: ["dept-officers", departmentId] });

    },

  });



  if (complaint.assigned_officer_id && complaint.assigned_officer_name) {

    return (

      <section className="rounded-xl border bg-card p-4 shadow-sm">

        <div className="flex items-center gap-2 text-sm">

          <UserCheck className="h-4 w-4 text-primary" />

          <span>

            Assigned to <strong>{complaint.assigned_officer_name}</strong>

          </span>

        </div>

      </section>

    );

  }



  return (

    <section className="rounded-xl border border-blue-200 bg-blue-50/40 p-4 sm:p-5 shadow-sm space-y-4">

      <div>

        <h2 className="text-sm font-semibold">Assign field officer</h2>

        <p className="text-xs text-muted-foreground mt-1">

          Review each officer&apos;s field area and active cases by priority, then select who should take this complaint.

        </p>

      </div>



      {isLoading ? (

        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />

      ) : officers.length === 0 ? (

        <p className="text-sm text-amber-800">No officers in this department. Add one under Field team or Staff.</p>

      ) : (

        <>

          <div className="space-y-2 max-h-[min(420px,50vh)] overflow-y-auto pr-1">

            {officers.map((o) => {

              const selectedCard = officerId === o.id;

              const total = o.active_assigned_count ?? 0;

              return (

                <button

                  key={o.id}

                  type="button"

                  onClick={() => setOfficerId(o.id)}

                  className={cn(

                    "w-full text-left rounded-xl border bg-white p-4 transition-shadow",

                    selectedCard ? "border-primary ring-2 ring-primary/30 shadow-sm" : "border-border hover:border-primary/40"

                  )}

                >

                  <div className="flex items-start justify-between gap-2">

                    <div className="min-w-0">

                      <p className="font-semibold text-sm truncate">{o.full_name}</p>

                      {o.department_name && (

                        <p className="text-xs text-muted-foreground mt-0.5">{o.department_name}</p>

                      )}

                    </div>

                    <span className="shrink-0 text-xs font-medium text-primary bg-primary/10 rounded-full px-2 py-0.5">

                      {total} active

                    </span>

                  </div>



                  <p className="text-xs text-muted-foreground mt-2 flex items-start gap-1.5">

                    <MapPin className="h-3.5 w-3.5 shrink-0 mt-0.5 text-primary" />

                    <span className="min-w-0 flex-1 break-words whitespace-normal leading-relaxed [overflow-wrap:anywhere]">

                      <span className="font-medium text-foreground">Field area: </span>

                      {o.service_area?.trim() || "Not set"}

                    </span>

                  </p>



                  <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">

                    {o.email && (

                      <span className="inline-flex items-center gap-1 truncate max-w-full">

                        <Mail className="h-3 w-3 shrink-0" />

                        {o.email}

                      </span>

                    )}

                    {o.phone && (

                      <span className="inline-flex items-center gap-1">

                        <Phone className="h-3 w-3 shrink-0" />

                        {o.phone}

                      </span>

                    )}

                  </div>



                  <PriorityWorkload o={o} />

                </button>

              );

            })}

          </div>



          {selected && (

            <div className="rounded-lg border border-primary/20 bg-white/80 px-3 py-2 text-xs text-muted-foreground">

              Selected: <strong className="text-foreground">{selected.full_name}</strong>

              {" · "}

              {selected.active_assigned_count ?? 0} active case(s) before this assignment

            </div>

          )}



          <Button size="sm" className="w-full sm:w-auto" disabled={!officerId || assign.isPending} onClick={() => assign.mutate()}>

            {assign.isPending ? "Assigning…" : "Assign selected officer"}

          </Button>

        </>

      )}

    </section>

  );

}


